"""
笔记相关路由
提供小红书风格的笔记Feed、详情、相关推荐等功能
"""
from flask import Blueprint, request, jsonify, g
from models import db, Note, Tag, User, Like, Favorite, note_tags
import json
import os
import sys
import random

# 添加推荐引擎到路径
sys.path.append(os.path.join(os.path.dirname(__file__), '../../recommendation'))

try:
    from recommendation_engine import HybridRecommender, CollaborativeFiltering
    import pandas as pd
    RECOMMENDATION_AVAILABLE = True
except ImportError:
    RECOMMENDATION_AVAILABLE = False
    print("Warning: recommendation_engine not available")

notes_bp = Blueprint('notes', __name__)

# 全局推荐引擎实例
_recommender = None

def get_recommender():
    """获取或初始化推荐引擎"""
    global _recommender
    if _recommender is None and RECOMMENDATION_AVAILABLE:
        _recommender = HybridRecommender(cf_weight=0.5, cb_weight=0.5, exploration_rate=0.15)
    return _recommender


def get_current_user_id():
    """获取当前用户ID（从请求参数或请求头）"""
    # 首先尝试从请求参数获取
    user_id = request.args.get('user_id', type=int)
    if user_id:
        return user_id
    
    # 从请求头获取token（实际项目中）
    # 从request属性获取
    return getattr(request, 'user_id', None)


def get_user_behavior_history(user_id):
    """获取用户行为历史（浏览、点赞、收藏）"""
    # 获取用户点赞的笔记
    liked_notes = Like.query.filter_by(user_id=user_id).all()
    liked_ids = [like.note_id for like in liked_notes]
    
    # 获取用户收藏的笔记
    favorited_notes = Favorite.query.filter_by(user_id=user_id).all()
    favorited_ids = [fav.note_id for fav in favorited_notes]
    
    # 合并历史记录（去重）
    history_ids = list(set(liked_ids + favorited_ids))
    
    return {
        'liked': liked_ids,
        'favorited': favorited_ids,
        'all': history_ids
    }


def get_user_preferred_tags(user_id):
    """获取用户偏好的标签（基于历史行为）"""
    history = get_user_behavior_history(user_id)
    all_history_ids = history['all']
    
    if not all_history_ids:
        return []
    
    # 获取历史笔记的标签
    tag_counts = {}
    for note_id in all_history_ids[:20]:  # 只考虑最近20个
        note = Note.query.get(note_id)
        if note:
            for tag in note.tags:
                tag_counts[tag.name] = tag_counts.get(tag.name, 0) + 1
    
    # 按频次排序
    sorted_tags = sorted(tag_counts.items(), key=lambda x: x[1], reverse=True)
    return [tag[0] for tag in sorted_tags[:10]]  # 返回前10个偏好标签


def get_trending_feed(page=1, per_page=20):
    """获取热度排序的笔记（未登录用户使用）"""
    query = Note.query.filter_by(is_public=True, is_deleted=False)
    
    # 热度分数 = 点赞数*3 + 收藏数*2 + 评论数*2 + 浏览数*0.1
    query = query.order_by(
        (Note.like_count * 3 + Note.favorite_count * 2 + Note.comment_count * 2 + Note.view_count * 0.1).desc(),
        Note.created_at.desc()
    )
    
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)
    notes = pagination.items
    
    return {
        'items': [note.to_dict() for note in notes],
        'pagination': {
            'page': page,
            'per_page': per_page,
            'total': pagination.total,
            'pages': pagination.pages,
            'has_next': pagination.has_next,
            'has_prev': pagination.has_prev
        }
    }


def get_personalized_feed(user_id, page=1, per_page=20):
    """获取个性化推荐笔记（基于混合推荐算法）"""
    # 获取用户行为历史
    behavior = get_user_behavior_history(user_id)
    history_ids = behavior['all']
    
    # 如果有足够的历史数据，使用个性化推荐
    if len(history_ids) >= 3:
        # 基于用户偏好标签获取推荐
        preferred_tags = get_user_preferred_tags(user_id)
        
        # 查询候选笔记（排除已交互的）
        if history_ids:
            candidate_query = Note.query.filter(
                Note.is_public == True,
                Note.is_deleted == False,
                ~Note.id.in_(history_ids)
            )
        else:
            candidate_query = Note.query.filter(
                Note.is_public == True,
                Note.is_deleted == False
            )
        
        candidates = candidate_query.all()
        
        if candidates:
            # 计算每个候选笔记的匹配分数
            scored_notes = []
            for note in candidates:
                score = 0
                note_tags_list = [tag.name for tag in note.tags]
                
                # 标签匹配分数
                if preferred_tags and note_tags_list:
                    matching_tags = set(preferred_tags) & set(note_tags_list)
                    score += len(matching_tags) * 10
                
                # 热度分数（较低的权重）
                hot_score = (note.like_count * 2 + note.favorite_count + note.comment_count) / 100
                score += hot_score
                
                # 时间衰减（新内容加权）
                from datetime import datetime
                if note.created_at:
                    days_old = (datetime.utcnow() - note.created_at).days
                    time_boost = max(0, (30 - days_old) / 30) * 5  # 30天内的新内容有加分
                    score += time_boost
                
                scored_notes.append((note, score))
            
            # 按分数排序
            scored_notes.sort(key=lambda x: x[1], reverse=True)
            
            # 加入探索机制：15%随机内容
            n_explore = int(per_page * 0.15)
            n_exploit = per_page - n_explore
            
            # 选择高匹配度笔记
            exploit_notes = [n[0] for n in scored_notes[:n_exploit * 3]]  # 取更多用于分页
            
            # 随机选择探索内容（从非推荐内容中）
            explore_candidates = [n[0] for n in scored_notes[n_exploit * 3:]]
            if len(explore_candidates) > n_explore:
                explore_notes = random.sample(explore_candidates, n_explore)
            else:
                explore_notes = explore_candidates
            
            # 合并并打乱顺序
            recommended_notes = exploit_notes + explore_notes
            random.shuffle(recommended_notes)
        else:
            # 没有候选时返回热门
            return get_trending_feed(page, per_page)
    else:
        # 冷启动：返回热门内容
        trending = get_trending_feed(page, per_page)
        return trending
    
    # 分页处理
    start = (page - 1) * per_page
    end = start + per_page
    paginated_notes = recommended_notes[start:end]
    
    return {
        'items': [note.to_dict() for note in paginated_notes],
        'pagination': {
            'page': page,
            'per_page': per_page,
            'total': len(recommended_notes),
            'pages': (len(recommended_notes) + per_page - 1) // per_page,
            'has_next': end < len(recommended_notes),
            'has_prev': page > 1
        }
    }


def mock_auth_required(f):
    """Mock认证装饰器"""
    from functools import wraps
    @wraps(f)
    def decorated(*args, **kwargs):
        request.user_id = get_current_user_id() or 1
        return f(*args, **kwargs)
    return decorated


# ==================== 笔记Feed相关 ====================

@notes_bp.route('/notes/feed', methods=['GET'])
def get_notes_feed():
    """
    获取笔记Feed流（瀑布流）
    支持个性化推荐（登录用户）或热度排序（未登录用户）
    GET /api/notes/feed?page=1&per_page=20&user_id=xxx
    """
    try:
        # 获取分页参数
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        
        # 限制每页数量
        per_page = min(per_page, 50)
        if per_page < 1:
            per_page = 20
        if page < 1:
            page = 1
        
        # 获取用户ID（用于个性化推荐）
        user_id = get_current_user_id()
        
        if user_id:
            # 已登录用户：返回个性化推荐
            result = get_personalized_feed(user_id, page, per_page)
        else:
            # 未登录用户：返回热度排序
            result = get_trending_feed(page, per_page)
        
        return jsonify({
            'success': True, 
            'data': result,
            'personalized': user_id is not None  # 标记是否为个性化内容
        })
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500


@notes_bp.route('/notes/<int:note_id>', methods=['GET'])
def get_note_detail(note_id):
    """
    获取笔记详情
    GET /api/notes/<id>
    """
    try:
        note = Note.query.filter_by(
            id=note_id, 
            is_deleted=False
        ).first_or_404()
        
        # 如果不是公开笔记，需要检查权限
        if not note.is_public:
            # TODO: 检查是否是作者本人
            pass
        
        # 获取当前用户ID
        current_user_id = get_current_user_id()
        
        # 增加浏览计数
        note.view_count += 1
        db.session.commit()
        
        # 返回详情
        data = note.to_detail_dict(current_user_id=current_user_id)
        
        return jsonify({'success': True, 'data': data})
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500


@notes_bp.route('/notes/<int:note_id>/related', methods=['GET'])
def get_related_notes(note_id):
    """
    获取相关笔记（基于相同标签）
    GET /api/notes/<id>/related?limit=10
    """
    try:
        note = Note.query.filter_by(
            id=note_id, 
            is_deleted=False
        ).first_or_404()
        
        limit = request.args.get('limit', 10, type=int)
        limit = min(limit, 20)
        
        # 获取当前笔记的标签ID
        tag_ids = [tag.id for tag in note.tags]
        
        if not tag_ids:
            return jsonify({'success': True, 'data': [], 'message': '该笔记没有标签'})
        
        # 查询具有相同标签的其他笔记
        from models import note_tags
        
        related_query = Note.query.filter(
            Note.id != note_id,
            Note.is_public == True,
            Note.is_deleted == False
        ).join(
            note_tags,
            Note.id == note_tags.c.note_id
        ).filter(
            note_tags.c.tag_id.in_(tag_ids)
        ).group_by(Note.id).order_by(
            db.func.count(note_tags.c.tag_id).desc(),
            Note.like_count.desc()
        ).limit(limit)
        
        related_notes = related_query.all()
        
        return jsonify({
            'success': True, 
            'data': [n.to_dict() for n in related_notes],
            'count': len(related_notes)
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


# ==================== Tag相关 ====================

@notes_bp.route('/tags', methods=['GET'])
def get_tags():
    """
    获取热门标签列表
    GET /api/tags?limit=50&sort=hot
    """
    try:
        limit = request.args.get('limit', 50, type=int)
        sort = request.args.get('sort', 'hot', type=str)  # hot: 热门, name: 名称
        
        limit = min(limit, 100)
        
        query = Tag.query
        
        if sort == 'hot':
            query = query.order_by(Tag.usage_count.desc(), Tag.name.asc())
        else:
            query = query.order_by(Tag.name.asc())
        
        tags = query.limit(limit).all()
        
        return jsonify({
            'success': True,
            'data': [tag.to_dict() for tag in tags],
            'count': len(tags)
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@notes_bp.route('/tags/<string:tag_name>/notes', methods=['GET'])
def get_tag_notes(tag_name):
    """
    获取指定标签的笔记列表
    GET /api/tags/<tag>/notes?page=1&per_page=20
    """
    try:
        tag = Tag.query.filter_by(name=tag_name).first_or_404()
        
        # 获取分页参数
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        per_page = min(per_page, 50)
        
        # 查询该标签的公开笔记
        query = tag.notes.filter_by(is_public=True, is_deleted=False)
        query = query.order_by(Note.created_at.desc())
        
        pagination = query.paginate(page=page, per_page=per_page, error_out=False)
        notes = pagination.items
        
        data = {
            'tag': tag.to_dict(),
            'items': [note.to_dict() for note in notes],
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


# ==================== 笔记管理（需要登录） ====================

@notes_bp.route('/notes', methods=['POST'])
@mock_auth_required
def create_note():
    """
    创建笔记
    POST /api/notes
    """
    try:
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'error': '请求体不能为空'}), 400
        
        # 验证必填字段
        title = data.get('title', '').strip()
        content = data.get('content', '').strip()
        
        if not title:
            return jsonify({'success': False, 'error': '标题不能为空'}), 400
        if not content:
            return jsonify({'success': False, 'error': '内容不能为空'}), 400
        
        # 创建笔记
        note = Note(
            author_id=request.user_id,
            title=title,
            content=content,
            preview=data.get('preview', content[:200] + '...' if len(content) > 200 else content),
            paper_title=data.get('paper_title'),
            paper_authors=json.dumps(data.get('paper_authors', [])) if data.get('paper_authors') else None,
            paper_journal=data.get('paper_journal'),
            paper_pub_date=data.get('paper_pub_date'),
            paper_doi=data.get('paper_doi'),
            paper_pmid=data.get('paper_pmid'),
            paper_url=data.get('paper_url'),
            media_urls=json.dumps(data.get('media_urls', [])) if data.get('media_urls') else None,
            is_public=data.get('is_public', True)
        )
        
        # 处理标签
        tags = data.get('tags', [])
        if tags:
            for tag_name in tags:
                tag_name = tag_name.strip().lower()
                if tag_name:
                    tag = Tag.query.filter_by(name=tag_name).first()
                    if not tag:
                        tag = Tag(name=tag_name)
                        db.session.add(tag)
                    note.tags.append(tag)
                    tag.usage_count += 1
        
        db.session.add(note)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'data': note.to_detail_dict(current_user_id=request.user_id),
            'message': '笔记创建成功'
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500


@notes_bp.route('/notes/<int:note_id>', methods=['PUT'])
@mock_auth_required
def update_note(note_id):
    """
    更新笔记
    PUT /api/notes/<id>
    """
    try:
        note = Note.query.filter_by(id=note_id, is_deleted=False).first_or_404()
        
        # 检查权限
        if note.author_id != request.user_id:
            return jsonify({'success': False, 'error': '无权修改此笔记'}), 403
        
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'error': '请求体不能为空'}), 400
        
        # 更新字段
        if 'title' in data:
            note.title = data['title'].strip()
        if 'content' in data:
            note.content = data['content'].strip()
            note.preview = data.get('preview', note.content[:200] + '...' if len(note.content) > 200 else note.content)
        if 'paper_title' in data:
            note.paper_title = data['paper_title']
        if 'paper_authors' in data:
            note.paper_authors = json.dumps(data['paper_authors'])
        if 'is_public' in data:
            note.is_public = data['is_public']
        
        note.updated_at = db.func.now()
        db.session.commit()
        
        return jsonify({
            'success': True,
            'data': note.to_detail_dict(current_user_id=request.user_id),
            'message': '笔记更新成功'
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500


@notes_bp.route('/notes/<int:note_id>', methods=['DELETE'])
@mock_auth_required
def delete_note(note_id):
    """
    删除笔记（软删除）
    DELETE /api/notes/<id>
    """
    try:
        note = Note.query.filter_by(id=note_id, is_deleted=False).first_or_404()
        
        # 检查权限
        if note.author_id != request.user_id:
            return jsonify({'success': False, 'error': '无权删除此笔记'}), 403
        
        # 软删除
        note.is_deleted = True
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': '笔记删除成功'
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500


# ==================== 用户笔记列表 ====================

@notes_bp.route('/users/<int:user_id>/notes', methods=['GET'])
def get_user_notes(user_id):
    """
    获取用户发布的笔记列表
    GET /api/users/<user_id>/notes?page=1&per_page=20
    """
    try:
        user = User.query.get_or_404(user_id)
        
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        per_page = min(per_page, 50)
        
        # 只显示公开的笔记
        query = Note.query.filter_by(
            author_id=user_id,
            is_public=True,
            is_deleted=False
        ).order_by(Note.created_at.desc())
        
        pagination = query.paginate(page=page, per_page=per_page, error_out=False)
        notes = pagination.items
        
        data = {
            'author': {
                'id': user.id,
                'username': user.username,
                'avatar_url': user.avatar_url
            },
            'items': [note.to_dict() for note in notes],
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
