"""
ProteinHub User Model
用户数据模型定义
"""
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import bcrypt

db = SQLAlchemy()

class User(db.Model):
    """
    用户模型
    
    Attributes:
        id: 用户唯一标识
        username: 用户名
        email: 邮箱地址（唯一）
        password_hash: bcrypt加密的密码
        is_active: 账户是否激活
        created_at: 注册时间
        updated_at: 最后更新时间
    """
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(128), nullable=False)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 用户关注的蛋白列表（多对多关系）
    followed_proteins = db.relationship(
        'Protein',
        secondary='user_protein_follows',
        backref='followers'
    )
    
    def __init__(self, username, email, password):
        """
        创建新用户
        
        Args:
            username: 用户名
            email: 邮箱地址
            password: 明文密码（会自动bcrypt加密）
        """
        self.username = username
        self.email = email.lower().strip()
        self.password_hash = self._hash_password(password)
    
    def _hash_password(self, password):
        """
        使用bcrypt加密密码
        
        Args:
            password: 明文密码
            
        Returns:
            str: 加密后的密码hash
        """
        if isinstance(password, str):
            password = password.encode('utf-8')
        return bcrypt.hashpw(password, bcrypt.gensalt(rounds=12)).decode('utf-8')
    
    def verify_password(self, password):
        """
        验证密码是否正确
        
        Args:
            password: 待验证的明文密码
            
        Returns:
            bool: 密码是否正确
        """
        if isinstance(password, str):
            password = password.encode('utf-8')
        return bcrypt.checkpw(password, self.password_hash.encode('utf-8'))
    
    def to_dict(self, include_email=False):
        """
        将用户对象转换为字典
        
        Args:
            include_email: 是否包含邮箱地址
            
        Returns:
            dict: 用户信息字典（不含密码）
        """
        data = {
            'id': self.id,
            'username': self.username,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }
        if include_email:
            data['email'] = self.email
        return data
    
    def __repr__(self):
        return f'<User {self.username}>'


# 用户关注蛋白的中间表
user_protein_follows = db.Table(
    'user_protein_follows',
    db.Column('user_id', db.Integer, db.ForeignKey('users.id'), primary_key=True),
    db.Column('protein_id', db.Integer, db.ForeignKey('proteins.id'), primary_key=True),
    db.Column('followed_at', db.DateTime, default=datetime.utcnow)
)
