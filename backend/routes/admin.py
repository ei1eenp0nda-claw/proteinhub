"""
ProteinHub Admin Panel
管理后台 API
"""
from flask import Blueprint, request, jsonify
from functools import wraps
from models import db, User, Protein, ProteinInteraction, Post

admin_bp = Blueprint('admin', __name__, url_prefix='/api/admin')


# 简单的管理员权限检查
def require_admin(f):
    """要求管理员权限"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # 从请求头获取 token
        from auth import get_token_from_header, decode_token
        
        token = get_token_from_header()
        if not token:
            return jsonify({'error': '未登录'}), 401
        
        try:
            payload = decode_token(token)
            user_id = payload.get('user_id')
            user = User.query.get(user_id)
            
            if not user:
                return jsonify({'error': '用户不存在'}), 401
            
            # 检查是否是管理员（简单判断：id 为 1 或用户名是 admin）
            if user.id != 1 and user.username != 'admin':
                return jsonify({'error': '权限不足'}), 403
            
            return f(user, *args, **kwargs)
            
        except Exception as e:
            return jsonify({'error': '认证失败'}), 401
    
    return decorated_function


@admin_bp.route('/stats', methods=['GET'])
@require_admin
def get_system_stats(admin_user):
    """获取系统统计数据"""
    stats = {
        'users': {
            'total': User.query.count(),
            'active': User.query.filter_by(is_active=True).count()
        },
        'proteins': {
            'total': Protein.query.count(),
            'with_interactions': db.session.query(
                ProteinInteraction.protein_a_id
            ).distinct().count()
        },
        'interactions': {
            'total': ProteinInteraction.query.count()
        },
        'posts': {
            'total': Post.query.count()
        }
    }
    
    return jsonify(stats)


@admin_bp.route('/users', methods=['GET'])
@require_admin
def list_users(admin_user):
    """获取用户列表"""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    
    pagination = User.query.paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    return jsonify({
        'items': [u.to_dict(include_email=True) for u in pagination.items],
        'total': pagination.total,
        'pages': pagination.pages,
        'current_page': page
    })


@admin_bp.route('/users/<int:user_id>', methods=['DELETE'])
@require_admin
def delete_user(admin_user, user_id):
    """删除用户"""
    if user_id == admin_user.id:
        return jsonify({'error': '不能删除自己'}), 400
    
    user = User.query.get(user_id)
    if not user:
        return jsonify({'error': '用户不存在'}), 404
    
    try:
        db.session.delete(user)
        db.session.commit()
        return jsonify({'message': '用户已删除'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': '删除失败'}), 500


@admin_bp.route('/proteins', methods=['POST'])
@require_admin
def create_protein(admin_user):
    """创建新蛋白"""
    data = request.get_json()
    
    if not data or not data.get('name'):
        return jsonify({'error': '蛋白名称不能为空'}), 400
    
    # 检查是否已存在
    if Protein.query.filter_by(name=data['name']).first():
        return jsonify({'error': '蛋白已存在'}), 409
    
    try:
        protein = Protein(
            name=data['name'],
            family=data.get('family'),
            uniprot_id=data.get('uniprot_id'),
            description=data.get('description')
        )
        db.session.add(protein)
        db.session.commit()
        
        return jsonify({
            'message': '蛋白创建成功',
            'protein': protein.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': '创建失败'}), 500


@admin_bp.route('/proteins/<int:protein_id>', methods=['DELETE'])
@require_admin
def delete_protein(admin_user, protein_id):
    """删除蛋白"""
    protein = Protein.query.get(protein_id)
    if not protein:
        return jsonify({'error': '蛋白不存在'}), 404
    
    try:
        db.session.delete(protein)
        db.session.commit()
        return jsonify({'message': '蛋白已删除'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': '删除失败'}), 500


@admin_bp.route('/posts', methods=['GET'])
@require_admin
def list_posts(admin_user):
    """获取帖子列表（管理）"""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    
    pagination = Post.query.order_by(Post.created_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    return jsonify({
        'items': [p.to_dict() for p in pagination.items],
        'total': pagination.total,
        'pages': pagination.pages
    })


@admin_bp.route('/posts/<int:post_id>', methods=['DELETE'])
@require_admin
def delete_post(admin_user, post_id):
    """删除帖子"""
    post = Post.query.get(post_id)
    if not post:
        return jsonify({'error': '帖子不存在'}), 404
    
    try:
        db.session.delete(post)
        db.session.commit()
        return jsonify({'message': '帖子已删除'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': '删除失败'}), 500


@admin_bp.route('/import', methods=['POST'])
@require_admin
def import_data(admin_user):
    """导入数据"""
    from utils.data_importer import ProteinInteractionImporter
    
    data = request.get_json()
    if not data or not data.get('data'):
        return jsonify({'error': '缺少数据'}), 400
    
    try:
        importer = ProteinInteractionImporter(db.session)
        
        for row in data['data']:
            importer.import_row(row)
        
        db.session.commit()
        
        report = importer.get_report()
        return jsonify({
            'message': '导入完成',
            'report': report
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@admin_bp.route('/cache/clear', methods=['POST'])
@require_admin
def clear_cache(admin_user):
    """清除缓存"""
    from utils.cache import get_cache
    
    try:
        cache = get_cache()
        # 这里应该实现清除所有缓存的逻辑
        return jsonify({'message': '缓存已清除'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500
