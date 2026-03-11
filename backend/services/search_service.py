"""
ProteinHub Enhanced Search
高级搜索功能
支持全文搜索、模糊匹配、多字段联合搜索
"""
from sqlalchemy import or_, and_, func
from sqlalchemy.sql import text
from models import Protein, Post, ProteinInteraction


class SearchEngine:
    """搜索引擎"""
    
    def __init__(self, db_session):
        self.db = db_session
    
    def search_proteins(
        self,
        query: str,
        filters: dict = None,
        sort_by: str = 'relevance',
        page: int = 1,
        per_page: int = 20
    ):
        """
        高级蛋白搜索
        
        Args:
            query: 搜索关键词
            filters: 过滤条件 {family, has_interactions, min_score}
            sort_by: 排序方式 (relevance, name, date)
            page: 页码
            per_page: 每页数量
        """
        if not query or len(query.strip()) < 2:
            return self._empty_result()
        
        # 构建搜索查询
        search_terms = query.strip().split()
        
        # 基础查询
        base_query = self.db.query(Protein)
        
        # 多字段搜索
        conditions = []
        for term in search_terms:
            term_pattern = f'%{term}%'
            conditions.append(
                or_(
                    Protein.name.ilike(term_pattern),
                    Protein.description.ilike(term_pattern),
                    Protein.family.ilike(term_pattern),
                    Protein.uniprot_id.ilike(term_pattern)
                )
            )
        
        if conditions:
            base_query = base_query.filter(and_(*conditions))
        
        # 应用过滤
        if filters:
            if filters.get('family'):
                base_query = base_query.filter(
                    Protein.family == filters['family']
                )
            
            if filters.get('has_interactions'):
                # 筛选有互作的蛋白
                base_query = base_query.join(
                    ProteinInteraction,
                    or_(
                        Protein.id == ProteinInteraction.protein_a_id,
                        Protein.id == ProteinInteraction.protein_b_id
                    )
                ).distinct()
        
        # 排序
        if sort_by == 'name':
            base_query = base_query.order_by(Protein.name)
        elif sort_by == 'date':
            base_query = base_query.order_by(Protein.created_at.desc())
        else:  # relevance - 按名称匹配度排序
            # 名称完全匹配优先
            base_query = base_query.order_by(
                func.case(
                    (Protein.name.ilike(f'{query}%'), 1),
                    else_=2
                ),
                Protein.name
            )
        
        # 分页
        pagination = base_query.paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        # 计算相关性分数
        items = []
        for protein in pagination.items:
            score = self._calculate_relevance_score(protein, query)
            protein_dict = protein.to_dict()
            protein_dict['search_score'] = score
            items.append(protein_dict)
        
        # 按相关性排序
        if sort_by == 'relevance':
            items.sort(key=lambda x: x['search_score'], reverse=True)
        
        return {
            'items': items,
            'total': pagination.total,
            'pages': pagination.pages,
            'current_page': page,
            'per_page': per_page,
            'query': query
        }
    
    def _calculate_relevance_score(self, protein, query: str) -> float:
        """计算相关性分数"""
        score = 0.0
        query_lower = query.lower()
        
        # 名称匹配
        if protein.name:
            name_lower = protein.name.lower()
            if name_lower == query_lower:
                score += 1.0
            elif name_lower.startswith(query_lower):
                score += 0.8
            elif query_lower in name_lower:
                score += 0.6
        
        # 描述匹配
        if protein.description and query_lower in protein.description.lower():
            score += 0.3
        
        # 家族匹配
        if protein.family and query_lower in protein.family.lower():
            score += 0.2
        
        return min(score, 1.0)
    
    def search_posts(
        self,
        query: str,
        protein_id: int = None,
        page: int = 1,
        per_page: int = 20
    ):
        """
        搜索帖子
        
        Args:
            query: 搜索关键词
            protein_id: 限制特定蛋白的帖子
            page: 页码
            per_page: 每页数量
        """
        if not query or len(query.strip()) < 2:
            return self._empty_result()
        
        base_query = self.db.query(Post)
        
        # 标题和摘要搜索
        search_pattern = f'%{query.strip()}%'
        base_query = base_query.filter(
            or_(
                Post.title.ilike(search_pattern),
                Post.summary.ilike(search_pattern)
            )
        )
        
        # 蛋白筛选
        if protein_id:
            base_query = base_query.filter(Post.protein_id == protein_id)
        
        # 排序：按时间倒序
        base_query = base_query.order_by(Post.created_at.desc())
        
        pagination = base_query.paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        return {
            'items': [p.to_dict() for p in pagination.items],
            'total': pagination.total,
            'pages': pagination.pages,
            'current_page': page,
            'per_page': per_page,
            'query': query
        }
    
    def fuzzy_search(self, query: str, limit: int = 10):
        """
        模糊搜索（支持拼写错误）
        
        使用 pg_trgm 扩展的相似度搜索
        """
        try:
            # 使用 PostgreSQL 的相似度搜索
            sql = text("""
                SELECT id, name, family, description,
                       similarity(name, :query) as sml
                FROM proteins
                WHERE name % :query
                   OR description % :query
                ORDER BY sml DESC, name
                LIMIT :limit
            """)
            
            result = self.db.execute(
                sql,
                {'query': query, 'limit': limit}
            )
            
            items = []
            for row in result:
                items.append({
                    'id': row[0],
                    'name': row[1],
                    'family': row[2],
                    'description': row[3],
                    'similarity': round(float(row[4]), 3)
                })
            
            return {'items': items, 'query': query}
            
        except Exception as e:
            # 如果 pg_trgm 未启用，回退到普通搜索
            result = self.search_proteins(query, per_page=limit)
            return {
                'items': result['items'],
                'query': query,
                'note': 'Fuzzy search not available, using exact match'
            }
    
    def autocomplete(self, query: str, limit: int = 10):
        """
        自动补全建议
        
        Args:
            query: 输入前缀
            limit: 返回数量
        """
        if not query or len(query) < 2:
            return {'suggestions': []}
        
        # 蛋白名称补全
        proteins = self.db.query(Protein).filter(
            Protein.name.ilike(f'{query}%')
        ).order_by(Protein.name).limit(limit).all()
        
        suggestions = []
        for p in proteins:
            suggestions.append({
                'type': 'protein',
                'value': p.name,
                'id': p.id,
                'family': p.family
            })
        
        # 家族名称补全
        families = self.db.query(Protein.family).filter(
            Protein.family.ilike(f'{query}%')
        ).distinct().limit(5).all()
        
        for f in families:
            if f[0]:
                suggestions.append({
                    'type': 'family',
                    'value': f[0]
                })
        
        return {
            'suggestions': suggestions,
            'query': query
        }
    
    def search_interactions(
        self,
        protein_name: str,
        min_score: float = 0.5,
        page: int = 1,
        per_page: int = 20
    ):
        """
        搜索蛋白互作
        
        Args:
            protein_name: 蛋白名称
            min_score: 最小互作分数
            page: 页码
            per_page: 每页数量
        """
        # 查找蛋白
        protein = self.db.query(Protein).filter(
            Protein.name.ilike(f'%{protein_name}%')
        ).first()
        
        if not protein:
            return self._empty_result()
        
        # 查找互作
        from sqlalchemy import or_
        
        query = self.db.query(
            ProteinInteraction,
            Protein
        ).join(
            Protein,
            or_(
                and_(
                    ProteinInteraction.protein_a_id == protein.id,
                    ProteinInteraction.protein_b_id == Protein.id
                ),
                and_(
                    ProteinInteraction.protein_b_id == protein.id,
                    ProteinInteraction.protein_a_id == Protein.id
                )
            )
        ).filter(
            ProteinInteraction.interaction_score >= min_score
        ).order_by(
            ProteinInteraction.interaction_score.desc()
        )
        
        pagination = query.paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        items = []
        for interaction, partner in pagination.items:
            items.append({
                'protein': partner.to_dict(),
                'interaction_score': interaction.interaction_score
            })
        
        return {
            'items': items,
            'total': pagination.total,
            'pages': pagination.pages,
            'current_page': page,
            'protein': protein.to_dict()
        }
    
    def _empty_result(self):
        """空结果"""
        return {
            'items': [],
            'total': 0,
            'pages': 0,
            'current_page': 1,
            'per_page': 20
        }


class SearchService:
    """搜索服务"""
    
    @staticmethod
    def get_search_suggestions(query: str, db_session):
        """获取搜索建议"""
        engine = SearchEngine(db_session)
        return engine.autocomplete(query)
    
    @staticmethod
    def search_all(query: str, db_session, page: int = 1):
        """全局搜索"""
        engine = SearchEngine(db_session)
        
        # 同时搜索蛋白和帖子
        proteins = engine.search_proteins(query, page=page, per_page=10)
        posts = engine.search_posts(query, page=page, per_page=10)
        
        return {
            'proteins': proteins,
            'posts': posts,
            'query': query
        }
