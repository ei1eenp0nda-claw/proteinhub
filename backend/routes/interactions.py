"""
互动相关路由
提供点赞、收藏、评论等互动功能
"""
from flask import Blueprint, request, jsonify
from models import db, Note, Like, Favorite, Comment

interactions_bp = Blueprint('interactions', __name__)


def get_current_user_id():
    """获取当前用户ID（Mock认证）"""
    return getattr(request, 'user_id', None) or 1


def mock_auth_required(f):
    """Mock认证装饰器"""
    from functools import wraps
    @wraps(f)
    def decorated(*args, **kwargs):
        request.user_id = get_current_user_id()
        return f(*args, **kwargs)
    return decorated


# ==================== 点赞相关 ====================

@interactions_bp.route('/notes/<int:note_id>/like', methods=['POST'])
@mock_auth_required
def toggle_like(note_id):
    """
    点赞/取消点赞（Toggle）
    POST /api/notes/<id>/like
    """
    try:
        user_id = request.user_id
        
        # 检查笔记是否存在且未删除
        note = Note.query.filter_by(id=note_id, is_deleted=False).first_or_404()
        
        # 检查是否已经点赞
        existing_like = Like.query.filter_by(
            user_id=user_id,
            note_id=note_id
        ).first()
        
        if existing_like:
            # 取消点赞
            db.session.delete(existing_like)
            note.like_count = max(0, note.like_count - 1)
            is_liked = False
            message = '取消点赞成功'
        else:
            # 添加点赞
            like = Like(user_id=user_id, note_id=note_id)
            db.session.add(like)
            note.like_count += 1
            is_liked = True
            message = '点赞成功'
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'data': {
                'is_liked': is_liked,
                'like_count': note.like_count
            },
            'message': message
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500


@interactions_bp.route('/notes/<int:note_id>/like', methods=['GET'])
def get_like_status(note_id):
    """
    获取点赞状态
    GET /api/notes/<id>/like
    """
    try:
        note = Note.query.filter_by(id=note_id, is_deleted=False).first_or_404()
        
        user_id = get_current_user_id()
        is_liked = False
        
        if user_id:
            is_liked = Like.query.filter_by(
                user_id=user_id,
                note_id=note_id
            ).first() is not None
        
        return jsonify({
            'success': True,
            'data': {
                'is_liked': is_liked,
                'like_count': note.like_count
            }
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


# ==================== 收藏相关 ====================

@interactions_bp.route('/notes/<int:note_id>/favorite', methods=['POST'])
@mock_auth_required
def toggle_favorite(note_id):
    """
    收藏/取消收藏（Toggle）
    POST /api/notes/<id>/favorite
    """
    try:
        user_id = request.user_id
        
        # 检查笔记是否存在且未删除
        note = Note.query.filter_by(id=note_id, is_deleted=False).first_or_404()
        
        # 检查是否已经收藏
        existing_favorite = Favorite.query.filter_by(
            user_id=user_id,
            note_id=note_id
        ).first()
        
        if existing_favorite:
            # 取消收藏
            db.session.delete(existing_favorite)
            note.favorite_count = max(0, note.favorite_count - 1)
            is_favorited = False
            message = '取消收藏成功'
        else:
            # 添加收藏
            favorite = Favorite(user_id=user_id, note_id=note_id)
            db.session.add(favorite)
            note.favorite_count += 1
            is_favorited = True
            message = '收藏成功'
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'data': {
                'is_favorited': is_favorited,
                'favorite_count': note.favorite_count
            },
            'message': message
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500


@interactions_bp.route('/notes/<int:note_id>/favorite', methods=['GET'])
def get_favorite_status(note_id):
    """
    获取收藏状态
    GET /api/notes/<id>/favorite
    """
    try:
        note = Note.query.filter_by(id=note_id, is_deleted=False).first_or_404()
        
        user_id = get_current_user_id()
        is_favorited = False
        
        if user_id:
            is_favorited = Favorite.query.filter_by(
                user_id=user_id,
                note_id=note_id
            ).first() is not None
        
        return jsonify({
            'success': True,
            'data': {
                'is_favorited': is_favorited,
                'favorite_count': note.favorite_count
            }
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


# ==================== 评论相关 ====================

@interactions_bp.route('/notes/<int:note_id>/comments', methods=['GET'])
def get_comments(note_id):
    """
    获取评论列表
    GET /api/notes/<id>/comments?page=1&per_page=20&sort=newest
    """
    try:
        # 检查笔记是否存在
        note = Note.query.filter_by(id=note_id, is_deleted=False).first_or_404()
        
        # 获取分页和排序参数
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        sort = request.args.get('sort', 'newest', type=str)  # newest: 最新, hottest: 最热
        
        per_page = min(per_page, 50)
        if page < 1:
            page = 1
        
        # 构建查询（只查询一级评论，不包含回复）
        query = Comment.query.filter_by(
            note_id=note_id,
            parent_id=None,  # 只获取一级评论
            is_deleted=False
        )
        
        # 排序
        if sort == 'hottest':
            query = query.order_by(Comment.like_count.desc(), Comment.created_at.desc())
        else:
            query = query.order_by(Comment.created_at.desc())
        
        # 分页
        pagination = query.paginate(page=page, per_page=per_page, error_out=False)
        comments = pagination.items
        
        # 获取每条评论的回复（最多3条）
        result = []
        for comment in comments:
            comment_data = comment.to_dict()
            
            # 获取该评论的回复
            replies = Comment.query.filter_by(
                parent_id=comment.id,
                is_deleted=False
            ).order_by(Comment.created_at.asc()).limit(3).all()
            
            comment_data['replies'] = [r.to_dict() for r in replies]
            comment_data['reply_count'] = Comment.query.filter_by(
                parent_id=comment.id,
                is_deleted=False
            ).count()
            
            result.append(comment_data)
        
        data = {
            'items': result,
            'pagination': {
                'page': page,
                'per_page': per_page,
                'total': pagination.total,
                'pages': pagination.pages,
                'has_next': pagination.has_next,
                'has_prev': pagination.has_prev
            }
        }
        
        return jsonify({'success': True, 'data': data})
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@interactions_bp.route('/notes/<int:note_id>/comments', methods=['POST'])
@mock_auth_required
def create_comment(note_id):
    """
    发布评论
    POST /api/notes/<id>/comments
    {
        "content": "评论内容",
        "parent_id": null  // 可选，回复某条评论
    }
    """
    try:
        user_id = request.user_id
        
        # 检查笔记是否存在且公开
        note = Note.query.filter_by(id=note_id, is_deleted=False).first_or_404()
        
        if not note.is_public:
            return jsonify({'success': False, 'error': '无法评论私密笔记'}), 403
        
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'error': '请求体不能为空'}), 400
        
        content = data.get('content', '').strip()
        if not content:
            return jsonify({'success': False, 'error': '评论内容不能为空'}), 400
        
        if len(content) > 1000:
            return jsonify({'success': False, 'error': '评论内容不能超过1000字'}), 400
        
        parent_id = data.get('parent_id')
        
        # 如果parent_id存在，验证父评论是否存在
        if parent_id:
            parent_comment = Comment.query.filter_by(
                id=parent_id,
                note_id=note_id,
                is_deleted=False
            ).first()
            
            if not parent_comment:
                return jsonify({'success': False, 'error': '回复的评论不存在'}), 404
            
            # 不支持多级回复（只允许回复一级评论）
            if parent_comment.parent_id is not None:
                return jsonify({'success': False, 'error': '只能回复一级评论'}), 400
        
        # 创建评论
        comment = Comment(
            user_id=user_id,
            note_id=note_id,
            content=content,
            parent_id=parent_id
        )
        
        db.session.add(comment)
        note.comment_count += 1
        db.session.commit()
        
        return jsonify({
            'success': True,
            'data': comment.to_dict(),
            'message': '评论发布成功'
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500


@interactions_bp.route('/comments/<int:comment_id>', methods=['DELETE'])
@mock_auth_required
def delete_comment(comment_id):
    """
    删除评论
    DELETE /api/comments/<id>
    """
    try:
        user_id = request.user_id
        
        comment = Comment.query.filter_by(id=comment_id).first_or_404()
        
        # 检查权限（只能删除自己的评论）
        if comment.user_id != user_id:
            return jsonify({'success': False, 'error': '无权删除此评论'}), 403
        
        # 软删除
        comment.is_deleted = True
        
        # 减少笔记评论数
        note = Note.query.get(comment.note_id)
        if note:
            note.comment_count = max(0, note.comment_count - 1)
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': '评论删除成功'
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500


# ==================== 用户收藏列表 ====================

@interactions_bp.route('/users/<int:user_id>/favorites', methods=['GET'])
def get_user_favorites(user_id):
    """
    获取用户的收藏列表
    GET /api/users/<user_id>/favorites?page=1&per_page=20
    """
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        per_page = min(per_page, 50)
        
        # 查询用户的收藏
        query = Favorite.query.filter_by(user_id=user_id).join(
            Note, Favorite.note_id == Note.id
        ).filter(
            Note.is_deleted == False,
            Note.is_public == True
        ).order_by(Favorite.created_at.desc())
        
        pagination = query.paginate(page=page, per_page=per_page, error_out=False)
        favorites = pagination.items
        
        data = {
            'items': [f.note.to_dict() for f in favorites if f.note],
            'pagination': {
                'page': page,
                'per_page': per_page,
                'total': pagination.total,
                'pages': pagination.pages,
                'has_next': pagination.has_next,
                'has_prev': pagination.has_prev
            }
        }
        
        return jsonify({'success': True, 'data': data})
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


# ==================== 用户点赞列表 ====================

@interactions_bp.route('/users/<int:user_id>/likes', methods=['GET'])
def get_user_likes(user_id):
    """
    获取用户的点赞列表
    GET /api/users/<user_id>/likes?page=1&per_page=20
    """
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        per_page = min(per_page, 50)
        
        # 查询用户的点赞
        query = Like.query.filter_by(user_id=user_id).join(
            Note, Like.note_id == Note.id
        ).filter(
            Note.is_deleted == False,
            Note.is_public == True
        ).order_by(Like.created_at.desc())
        
        pagination = query.paginate(page=page, per_page=per_page, error_out=False)
        likes = pagination.items
        
        data = {
            'items': [l.note.to_dict() for l in likes if l.note],
            'pagination': {
                'page': page,
                'per_page': per_page,
                'total': pagination.total,
                'pages': pagination.pages,
                'has_next': pagination.has_next,
                'has_prev': pagination.has_prev
            }
        }
        
        return jsonify({'success': True, 'data': data})
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500
