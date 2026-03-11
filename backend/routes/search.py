"""
ProteinHub Search API Routes
搜索相关API路由
"""
from flask import Blueprint, request, jsonify
from services.search_service import SearchEngine, SearchService

search_bp = Blueprint('search', __name__, url_prefix='/api/search')


@search_bp.route('/suggestions', methods=['GET'])
def get_suggestions():
    """
    获取搜索建议（自动补全）
    
    Query参数:
        q: 搜索前缀
        limit: 返回数量（默认10）
    """
    query = request.args.get('q', '').strip()
    limit = request.args.get('limit', 10, type=int)
    
    if len(query) < 2:
        return jsonify({'suggestions': []})
    
    from models import db
    result = SearchEngine(db.session).autocomplete(query, limit)
    
    return jsonify(result)


@search_bp.route('', methods=['GET'])
def global_search():
    """
    全局搜索
    
    Query参数:
        q: 搜索关键词
        page: 页码（默认1）
        per_page: 每页数量（默认10）
    """
    query = request.args.get('q', '').strip()
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    
    if not query:
        return jsonify({
            'proteins': {'items': [], 'total': 0},
            'posts': {'items': [], 'total': 0},
            'query': ''
        })
    
    from models import db
    result = SearchService.search_all(query, db.session, page)
    
    return jsonify(result)


@search_bp.route('/proteins', methods=['GET'])
def search_proteins():
    """
    搜索蛋白
    
    Query参数:
        q: 搜索关键词
        family: 家族筛选
        sort: 排序方式 (relevance, name, date)
        page: 页码
        per_page: 每页数量
    """
    query = request.args.get('q', '').strip()
    family = request.args.get('family')
    sort_by = request.args.get('sort', 'relevance')
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    
    if not query:
        return jsonify({'items': [], 'total': 0, 'pages': 0})
    
    filters = {}
    if family:
        filters['family'] = family
    
    from models import db
    engine = SearchEngine(db.session)
    result = engine.search_proteins(
        query, filters=filters, sort_by=sort_by,
        page=page, per_page=per_page
    )
    
    return jsonify(result)


@search_bp.route('/posts', methods=['GET'])
def search_posts():
    """
    搜索帖子
    
    Query参数:
        q: 搜索关键词
        protein_id: 限制特定蛋白的帖子
        page: 页码
        per_page: 每页数量
    """
    query = request.args.get('q', '').strip()
    protein_id = request.args.get('protein_id', type=int)
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    
    if not query:
        return jsonify({'items': [], 'total': 0, 'pages': 0})
    
    from models import db
    engine = SearchEngine(db.session)
    result = engine.search_posts(query, protein_id, page, per_page)
    
    return jsonify(result)


@search_bp.route('/fuzzy', methods=['GET'])
def fuzzy_search():
    """
    模糊搜索（支持拼写错误）
    
    Query参数:
        q: 搜索关键词
        limit: 返回数量（默认10）
    """
    query = request.args.get('q', '').strip()
    limit = request.args.get('limit', 10, type=int)
    
    if not query:
        return jsonify({'items': []})
    
    from models import db
    engine = SearchEngine(db.session)
    result = engine.fuzzy_search(query, limit)
    
    return jsonify(result)


@search_bp.route('/interactions', methods=['GET'])
def search_interactions():
    """
    搜索蛋白互作
    
    Query参数:
        protein: 蛋白名称
        min_score: 最小互作分数（默认0.5）
        page: 页码
        per_page: 每页数量
    """
    protein_name = request.args.get('protein', '').strip()
    min_score = request.args.get('min_score', 0.5, type=float)
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    
    if not protein_name:
        return jsonify({'items': [], 'total': 0, 'protein': None})
    
    from models import db
    engine = SearchEngine(db.session)
    result = engine.search_interactions(protein_name, min_score, page, per_page)
    
    return jsonify(result)
