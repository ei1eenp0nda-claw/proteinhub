"""
ProteinHub Protein Service
蛋白质数据服务层
提供蛋白相关的业务逻辑和数据操作
"""
from sqlalchemy import or_, func
from models import Protein, ProteinInteraction, Post, db

class ProteinService:
    """蛋白质数据服务"""
    
    @staticmethod
    def get_proteins(page=1, per_page=20, family=None, search=None):
        """
        分页获取蛋白列表
        
        Args:
            page: 页码（从1开始）
            per_page: 每页数量
            family: 按家族筛选
            search: 搜索关键词
            
        Returns:
            dict: 包含蛋白列表和分页信息
        """
        query = Protein.query
        
        # 家族筛选
        if family:
            query = query.filter_by(family=family)
        
        # 搜索
        if search:
            search_pattern = f'%{search}%'
            query = query.filter(
                or_(
                    Protein.name.ilike(search_pattern),
                    Protein.description.ilike(search_pattern),
                    Protein.family.ilike(search_pattern)
                )
            )
        
        # 分页
        pagination = query.paginate(page=page, per_page=per_page, error_out=False)
        
        return {
            'items': [p.to_dict() for p in pagination.items],
            'total': pagination.total,
            'pages': pagination.pages,
            'current_page': page,
            'per_page': per_page
        }
    
    @staticmethod
    def get_protein_by_id(protein_id):
        """
        根据ID获取蛋白详情
        
        Args:
            protein_id: 蛋白ID
            
        Returns:
            Protein: 蛋白对象，不存在返回None
        """
        return Protein.query.get(protein_id)
    
    @staticmethod
    def get_protein_by_name(name):
        """
        根据名称获取蛋白
        
        Args:
            name: 蛋白名称
            
        Returns:
            Protein: 蛋白对象
        """
        return Protein.query.filter_by(name=name).first()
    
    @staticmethod
    def get_protein_profile(protein_id):
        """
        获取蛋白主页完整信息
        
        Args:
            protein_id: 蛋白ID
            
        Returns:
            dict: 包含蛋白信息、传记、帖子、互作蛋白
        """
        protein = Protein.query.get(protein_id)
        if not protein:
            return None
        
        # 获取相关帖子
        posts = Post.query.filter_by(protein_id=protein_id)\
                         .order_by(Post.created_at.desc())\
                         .limit(10).all()
        
        # 获取互作蛋白
        interactions = ProteinInteraction.query.filter(
            or_(
                ProteinInteraction.protein_a_id == protein_id,
                ProteinInteraction.protein_b_id == protein_id
            )
        ).limit(10).all()
        
        interaction_proteins = []
        for interaction in interactions:
            partner_id = (interaction.protein_b_id 
                         if interaction.protein_a_id == protein_id 
                         else interaction.protein_a_id)
            partner = Protein.query.get(partner_id)
            if partner:
                interaction_proteins.append({
                    'protein': partner.to_dict(),
                    'score': interaction.interaction_score
                })
        
        # 生成传记内容
        biography = {
            'title': f'{protein.name} 蛋白传记',
            'overview': protein.description or f'{protein.name} 是 {protein.family} 家族的重要成员。',
            'family_info': f'属于 {protein.family} 蛋白家族',
            'structure_summary': '蛋白质结构信息待补充'
        }
        
        return {
            'protein': protein.to_dict(),
            'biography': biography,
            'posts': [p.to_dict() for p in posts],
            'interactions': {
                'count': len(interaction_proteins),
                'partners': interaction_proteins
            }
        }
    
    @staticmethod
    def get_families():
        """
        获取所有蛋白家族列表
        
        Returns:
            list: 家族名称列表
        """
        families = db.session.query(Protein.family)\
                            .distinct()\
                            .filter(Protein.family.isnot(None))\
                            .all()
        return [f[0] for f in families if f[0]]
    
    @staticmethod
    def create_protein(name, family=None, uniprot_id=None, description=None):
        """
        创建新蛋白记录
        
        Args:
            name: 蛋白名称（必需）
            family: 家族
            uniprot_id: UniProt ID
            description: 描述
            
        Returns:
            tuple: (Protein对象, 错误信息)
        """
        # 检查名称是否已存在
        if Protein.query.filter_by(name=name).first():
            return None, '蛋白名称已存在'
        
        try:
            protein = Protein(
                name=name,
                family=family,
                uniprot_id=uniprot_id,
                description=description
            )
            db.session.add(protein)
            db.session.commit()
            return protein, None
        except Exception as e:
            db.session.rollback()
            return None, str(e)
    
    @staticmethod
    def update_protein(protein_id, **kwargs):
        """
        更新蛋白信息
        
        Args:
            protein_id: 蛋白ID
            **kwargs: 要更新的字段
            
        Returns:
            tuple: (是否成功, 错误信息)
        """
        protein = Protein.query.get(protein_id)
        if not protein:
            return False, '蛋白不存在'
        
        # 不允许更新名称（如果会造成冲突）
        if 'name' in kwargs and kwargs['name'] != protein.name:
            if Protein.query.filter_by(name=kwargs['name']).first():
                return False, '新名称已存在'
        
        try:
            for key, value in kwargs.items():
                if hasattr(protein, key):
                    setattr(protein, key, value)
            db.session.commit()
            return True, None
        except Exception as e:
            db.session.rollback()
            return False, str(e)
    
    @staticmethod
    def delete_protein(protein_id):
        """
        删除蛋白记录
        
        Args:
            protein_id: 蛋白ID
            
        Returns:
            tuple: (是否成功, 错误信息)
        """
        protein = Protein.query.get(protein_id)
        if not protein:
            return False, '蛋白不存在'
        
        try:
            db.session.delete(protein)
            db.session.commit()
            return True, None
        except Exception as e:
            db.session.rollback()
            return False, str(e)
