"""
ProteinHub Feed Service
Feed推荐服务层
实现双塔召回 + 简单排序
"""
from sqlalchemy import desc
from models import Protein, Post, ProteinInteraction, db
import random

class FeedService:
    """Feed推荐服务"""
    
    @staticmethod
    def get_feed(user_id=None, page=1, per_page=20, strategy='recent'):
        """
        获取推荐Feed
        
        Args:
            user_id: 用户ID（可选，用于个性化）
            page: 页码
            per_page: 每页数量
            strategy: 推荐策略 ('recent', 'popular', 'random', 'personalized')
            
        Returns:
            dict: Feed数据
        """
        if strategy == 'recent':
            return FeedService._get_recent_feed(page, per_page)
        elif strategy == 'popular':
            return FeedService._get_popular_feed(page, per_page)
        elif strategy == 'random':
            return FeedService._get_random_feed(page, per_page)
        else:
            # 默认按时间倒序
            return FeedService._get_recent_feed(page, per_page)
    
    @staticmethod
    def _get_recent_feed(page, per_page):
        """获取最新帖子"""
        pagination = Post.query.order_by(desc(Post.created_at))\
                              .paginate(page=page, per_page=per_page, error_out=False)
        
        return {
            'items': [p.to_dict() for p in pagination.items],
            'total': pagination.total,
            'pages': pagination.pages,
            'current_page': page,
            'per_page': per_page,
            'strategy': 'recent'
        }
    
    @staticmethod
    def _get_popular_feed(page, per_page):
        """获取热门帖子（MVP：按标题长度排序作为热度指标）"""
        # TODO: 实际应根据点赞、收藏、评论数排序
        pagination = Post.query.order_by(desc(Post.id))\
                              .paginate(page=page, per_page=per_page, error_out=False)
        
        return {
            'items': [p.to_dict() for p in pagination.items],
            'total': pagination.total,
            'pages': pagination.pages,
            'current_page': page,
            'per_page': per_page,
            'strategy': 'popular'
        }
    
    @staticmethod
    def _get_random_feed(page, per_page):
        """随机获取帖子（冷启动策略）"""
        # 获取总数量
        total = Post.query.count()
        if total == 0:
            return {'items': [], 'total': 0, 'pages': 0, 'current_page': page, 'per_page': per_page}
        
        # 随机偏移
        offset = random.randint(0, max(0, total - per_page))
        posts = Post.query.offset(offset).limit(per_page).all()
        
        return {
            'items': [p.to_dict() for p in posts],
            'total': total,
            'pages': (total + per_page - 1) // per_page,
            'current_page': page,
            'per_page': per_page,
            'strategy': 'random'
        }
    
    @staticmethod
    def get_recommended_proteins(user_id=None, limit=10):
        """
        获取推荐蛋白（用于冷启动引导）
        
        Args:
            user_id: 用户ID
            limit: 返回数量
            
        Returns:
            list: 蛋白列表
        """
        # MVP：返回各个家族的代表蛋白
        proteins = []
        
        # 获取所有家族
        families = db.session.query(Protein.family).distinct().all()
        families = [f[0] for f in families if f[0]]
        
        # 每个家族取一个代表性蛋白
        for family in families[:limit]:
            protein = Protein.query.filter_by(family=family).first()
            if protein:
                proteins.append(protein.to_dict())
        
        # 如果不够，随机补充
        if len(proteins) < limit:
            remaining = limit - len(proteins)
            random_proteins = Protein.query.order_by(db.func.random()).limit(remaining).all()
            for p in random_proteins:
                if p.to_dict() not in proteins:
                    proteins.append(p.to_dict())
        
        return proteins[:limit]
    
    @staticmethod
    def search_posts(query, page=1, per_page=20):
        """
        搜索帖子
        
        Args:
            query: 搜索关键词
            page: 页码
            per_page: 每页数量
            
        Returns:
            dict: 搜索结果
        """
        if not query:
            return FeedService.get_feed(page=page, per_page=per_page)
        
        search_pattern = f'%{query}%'
        pagination = Post.query.filter(
            db.or_(
                Post.title.ilike(search_pattern),
                Post.summary.ilike(search_pattern)
            )
        ).order_by(desc(Post.created_at))\
         .paginate(page=page, per_page=per_page, error_out=False)
        
        return {
            'items': [p.to_dict() for p in pagination.items],
            'total': pagination.total,
            'pages': pagination.pages,
            'current_page': page,
            'per_page': per_page,
            'query': query
        }
