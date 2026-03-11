"""
ProteinHub Recommendation API Routes
推荐系统API路由
"""
from flask import Blueprint, request, jsonify
from models import Protein, User
from auth import require_auth, optional_auth
from recommendation.dual_tower import DualTowerRecommender, SimpleRecommender
from services.protein_service import ProteinService

rec_bp = Blueprint('recommendation', __name__, url_prefix='/api/recommend')

# 全局推荐模型实例
recommender = None
simple_recommender = SimpleRecommender()


def init_recommender(app, db):
    """初始化推荐模型"""
    global recommender
    with app.app_context():
        proteins = Protein.query.all()
        if proteins:
            recommender = DualTowerRecommender(embedding_dim=64)
            recommender.fit(proteins)
            app.recommender = recommender
            print(f"✅ 推荐模型初始化完成: {len(proteins)} 个蛋白")
        else:
            print("⚠️ 无蛋白数据，推荐模型未初始化")


@rec_bp.route('/personalized', methods=['GET'])
@require_auth
def get_personalized_recommendations(current_user):
    """
    获取个性化推荐（需要登录）
    
    Query参数:
        top_k: 推荐数量 (默认10)
        
    Returns:
        {
            "recommendations": [...],
            "strategy": "dual_tower"
        }
    """
    top_k = request.args.get('top_k', 10, type=int)
    
    if recommender is None:
        # 使用简单推荐
        proteins = Protein.query.all()
        recs = simple_recommender.recommend_popular(proteins, top_k)
        strategy = 'popular'
    else:
        # 获取用户关注
        user_follows = current_user.followed_proteins if hasattr(current_user, 'followed_proteins') else []
        
        # 使用双塔模型推荐
        recs = recommender.recommend(
            current_user, 
            user_follows, 
            top_k=top_k
        )
        strategy = 'dual_tower'
    
    # 获取完整的蛋白信息
    recommendations = []
    for protein_id, score in recs:
        protein = ProteinService.get_protein_by_id(protein_id)
        if protein:
            protein_dict = protein.to_dict()
            protein_dict['recommend_score'] = round(float(score), 4)
            recommendations.append(protein_dict)
    
    return jsonify({
        'recommendations': recommendations,
        'strategy': strategy,
        'count': len(recommendations)
    })


@rec_bp.route('/by-protein/<int:protein_id>', methods=['GET'])
def get_similar_proteins(protein_id):
    """
    获取相似蛋白推荐
    
    Args:
        protein_id: 参考蛋白ID
        
    Query参数:
        top_k: 推荐数量 (默认5)
    """
    top_k = request.args.get('top_k', 5, type=int)
    
    proteins = Protein.query.all()
    recs = simple_recommender.recommend_by_family(protein_id, proteins, top_k)
    
    recommendations = []
    for pid, score in recs:
        protein = ProteinService.get_protein_by_id(pid)
        if protein:
            protein_dict = protein.to_dict()
            protein_dict['similarity_score'] = round(float(score), 4)
            recommendations.append(protein_dict)
    
    return jsonify({
        'based_on': protein_id,
        'recommendations': recommendations,
        'strategy': 'same_family'
    })


@rec_bp.route('/explore', methods=['GET'])
@optional_auth
def get_explore_recommendations(current_user):
    """
    探索推荐（用于发现新蛋白）
    
    Query参数:
        top_k: 推荐数量 (默认5)
    """
    top_k = request.args.get('top_k', 5, type=int)
    
    proteins = Protein.query.all()
    recs = simple_recommender.recommend_explore(proteins, top_k)
    
    recommendations = []
    for pid, score in recs:
        protein = ProteinService.get_protein_by_id(pid)
        if protein:
            protein_dict = protein.to_dict()
            protein_dict['explore_score'] = round(float(score), 4)
            recommendations.append(protein_dict)
    
    return jsonify({
        'recommendations': recommendations,
        'strategy': 'explore_diverse_families'
    })


@rec_bp.route('/cold-start', methods=['POST'])
def get_cold_start_recommendations():
    """
    冷启动推荐（新用户引导）
    
    请求体:
        {
            "selected_families": ["CIDE", "PLIN", ...]  // 用户感兴趣的家族
        }
        
    Returns:
        {
            "recommendations": [...],
            "strategy": "cold_start"
        }
    """
    data = request.get_json() or {}
    selected_families = data.get('selected_families', [])
    top_k = data.get('top_k', 10)
    
    if not selected_families:
        # 如果没有选择，返回热门
        proteins = Protein.query.all()
        recs = simple_recommender.recommend_popular(proteins, top_k)
        strategy = 'popular'
    elif recommender is not None:
        # 使用双塔模型冷启动推荐
        recs = recommender.recommend_for_new_user(selected_families, top_k)
        strategy = 'dual_tower_cold_start'
    else:
        # 基于家族选择推荐
        proteins = Protein.query.filter(
            Protein.family.in_(selected_families)
        ).limit(top_k).all()
        recs = [(p.id, 1.0) for p in proteins]
        strategy = 'family_based'
    
    recommendations = []
    for pid, score in recs:
        protein = ProteinService.get_protein_by_id(pid)
        if protein:
            protein_dict = protein.to_dict()
            protein_dict['recommend_score'] = round(float(score), 4)
            recommendations.append(protein_dict)
    
    return jsonify({
        'recommendations': recommendations,
        'based_on_families': selected_families,
        'strategy': strategy
    })


@rec_bp.route('/model/status', methods=['GET'])
def get_model_status():
    """获取推荐模型状态"""
    return jsonify({
        'model_type': 'dual_tower' if recommender else 'simple',
        'is_fitted': recommender.is_fitted if recommender else False,
        'embedding_dim': recommender.embedding_dim if recommender else None,
        'n_items': len(recommender.item_embeddings) if recommender else 0,
        'n_users': len(recommender.user_embeddings) if recommender else 0
    })
