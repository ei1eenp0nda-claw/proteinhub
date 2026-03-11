"""
ProteinHub User Follow API
用户关注蛋白功能
"""
from flask import Blueprint, request, jsonify
from models import Protein, User, db
from auth import require_auth

follow_bp = Blueprint('follow', __name__, url_prefix='/api')


@follow_bp.route('/proteins/<int:protein_id>/follow', methods=['POST'])
@require_auth
def follow_protein(current_user, protein_id):
    """
    关注蛋白
    
    Args:
        protein_id: 蛋白ID
        
    Returns:
        {
            "message": "关注成功",
            "protein_id": int,
            "followed_at": "ISO时间"
        }
    """
    protein = Protein.query.get(protein_id)
    if not protein:
        return jsonify({'error': '蛋白不存在'}), 404
    
    # 检查是否已经关注
    if protein in current_user.followed_proteins:
        return jsonify({
            'message': '已经关注该蛋白',
            'protein_id': protein_id
        }), 200
    
    try:
        current_user.followed_proteins.append(protein)
        db.session.commit()
        
        return jsonify({
            'message': '关注成功',
            'protein_id': protein_id,
            'protein_name': protein.name,
            'followed_at': __import__('datetime').datetime.utcnow().isoformat()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': '关注失败'}), 500


@follow_bp.route('/proteins/<int:protein_id>/unfollow', methods=['DELETE'])
@require_auth
def unfollow_protein(current_user, protein_id):
    """
    取消关注蛋白
    
    Args:
        protein_id: 蛋白ID
    """
    protein = Protein.query.get(protein_id)
    if not protein:
        return jsonify({'error': '蛋白不存在'}), 404
    
    if protein not in current_user.followed_proteins:
        return jsonify({
            'message': '未关注该蛋白',
            'protein_id': protein_id
        }), 200
    
    try:
        current_user.followed_proteins.remove(protein)
        db.session.commit()
        
        return jsonify({
            'message': '取消关注成功',
            'protein_id': protein_id
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': '取消关注失败'}), 500


@follow_bp.route('/user/followed-proteins', methods=['GET'])
@require_auth
def get_followed_proteins(current_user):
    """
    获取当前用户关注的蛋白列表
    
    Query参数:
        page: 页码 (默认1)
        per_page: 每页数量 (默认20)
    """
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    
    # 手动分页
    followed = current_user.followed_proteins
    total = len(followed)
    
    start = (page - 1) * per_page
    end = start + per_page
    paginated = followed[start:end]
    
    return jsonify({
        'items': [p.to_dict() for p in paginated],
        'total': total,
        'pages': (total + per_page - 1) // per_page,
        'current_page': page,
        'per_page': per_page
    })


@follow_bp.route('/proteins/<int:protein_id>/is-followed', methods=['GET'])
@require_auth
def check_follow_status(current_user, protein_id):
    """
    检查是否已关注某蛋白
    
    Returns:
        {
            "is_followed": bool,
            "protein_id": int
        }
    """
    protein = Protein.query.get(protein_id)
    if not protein:
        return jsonify({'error': '蛋白不存在'}), 404
    
    is_followed = protein in current_user.followed_proteins
    
    return jsonify({
        'is_followed': is_followed,
        'protein_id': protein_id
    })


@follow_bp.route('/user/follow-feed', methods=['GET'])
@require_auth
def get_follow_feed(current_user):
    """
    获取关注蛋白的Feed（只看关注的蛋白的帖子）
    
    Query参数:
        page: 页码
        per_page: 每页数量
    """
    from models import Post
    from sqlalchemy import desc
    
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    
    if not current_user.followed_proteins:
        return jsonify({
            'items': [],
            'total': 0,
            'pages': 0,
            'current_page': page,
            'per_page': per_page,
            'message': '还没有关注任何蛋白'
        })
    
    # 获取关注蛋白的ID列表
    followed_ids = [p.id for p in current_user.followed_proteins]
    
    # 查询这些蛋白的帖子
    pagination = Post.query.filter(
        Post.protein_id.in_(followed_ids)
    ).order_by(
        desc(Post.created_at)
    ).paginate(page=page, per_page=per_page, error_out=False)
    
    return jsonify({
        'items': [p.to_dict() for p in pagination.items],
        'total': pagination.total,
        'pages': pagination.pages,
        'current_page': page,
        'per_page': per_page
    })
