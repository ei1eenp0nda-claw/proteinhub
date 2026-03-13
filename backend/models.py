"""
共享模型定义
避免循环导入
"""
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from datetime import datetime
import os

# 创建应用
app = Flask(__name__)
CORS(app)

# 配置
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'sqlite:///proteinhub.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# 笔记-标签关联表
note_tags = db.Table('note_tags',
    db.Column('note_id', db.Integer, db.ForeignKey('notes.id'), primary_key=True),
    db.Column('tag_id', db.Integer, db.ForeignKey('tags.id'), primary_key=True)
)


class Protein(db.Model):
    """蛋白质模型"""
    __tablename__ = 'proteins'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)
    family = db.Column(db.String(50))
    uniprot_id = db.Column(db.String(20))
    description = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'family': self.family,
            'uniprot_id': self.uniprot_id,
            'description': self.description
        }


class ProteinInteraction(db.Model):
    """蛋白质相互作用模型"""
    __tablename__ = 'protein_interactions'
    id = db.Column(db.Integer, primary_key=True)
    protein_a_id = db.Column(db.Integer, db.ForeignKey('proteins.id'))
    protein_b_id = db.Column(db.Integer, db.ForeignKey('proteins.id'))
    interaction_score = db.Column(db.Float)


class Post(db.Model):
    """帖子模型"""
    __tablename__ = 'posts'
    id = db.Column(db.Integer, primary_key=True)
    protein_id = db.Column(db.Integer, db.ForeignKey('proteins.id'))
    title = db.Column(db.String(500), nullable=False)
    summary = db.Column(db.Text)
    source_url = db.Column(db.String(500))
    source_title = db.Column(db.String(500))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    protein = db.relationship('Protein', backref='posts')
    
    def to_dict(self):
        return {
            'id': self.id,
            'protein_id': self.protein_id,
            'protein_name': self.protein.name if self.protein else None,
            'title': self.title,
            'summary': self.summary,
            'source_url': self.source_url,
            'created_at': self.created_at.isoformat()
        }


class User(db.Model):
    """用户模型"""
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(128), nullable=False)
    avatar_url = db.Column(db.String(500))
    bio = db.Column(db.Text)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    notes = db.relationship('Note', backref='author', lazy='dynamic')
    likes = db.relationship('Like', backref='user', lazy='dynamic')
    favorites = db.relationship('Favorite', backref='user', lazy='dynamic')
    comments = db.relationship('Comment', backref='user', lazy='dynamic')
    
    def __init__(self, username, email, password):
        self.username = username
        self.email = email.lower().strip()
        import bcrypt
        pwd = password.encode('utf-8') if isinstance(password, str) else password
        self.password_hash = bcrypt.hashpw(pwd, bcrypt.gensalt(rounds=12)).decode('utf-8')
    
    def to_dict(self, include_email=False):
        data = {
            'id': self.id,
            'username': self.username,
            'avatar_url': self.avatar_url,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }
        if include_email:
            data['email'] = self.email
        return data


class Tag(db.Model):
    """标签模型"""
    __tablename__ = 'tags'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False, index=True)
    description = db.Column(db.String(200))
    usage_count = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'usage_count': self.usage_count
        }


class Note(db.Model):
    """笔记模型"""
    __tablename__ = 'notes'
    
    id = db.Column(db.Integer, primary_key=True)
    author_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text, nullable=False)
    preview = db.Column(db.Text)
    
    paper_title = db.Column(db.String(500))
    paper_authors = db.Column(db.Text)
    paper_journal = db.Column(db.String(200))
    paper_pub_date = db.Column(db.String(50))
    paper_doi = db.Column(db.String(100))
    paper_pmid = db.Column(db.String(20))
    paper_url = db.Column(db.String(500))
    
    media_urls = db.Column(db.Text)
    
    view_count = db.Column(db.Integer, default=0)
    like_count = db.Column(db.Integer, default=0)
    favorite_count = db.Column(db.Integer, default=0)
    comment_count = db.Column(db.Integer, default=0)
    
    is_public = db.Column(db.Boolean, default=True)
    is_deleted = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    tags = db.relationship('Tag', secondary=note_tags, backref=db.backref('notes', lazy='dynamic'))
    likes = db.relationship('Like', backref='note', lazy='dynamic', cascade='all, delete-orphan')
    favorites = db.relationship('Favorite', backref='note', lazy='dynamic', cascade='all, delete-orphan')
    comments = db.relationship('Comment', backref='note', lazy='dynamic', cascade='all, delete-orphan')
    
    def to_dict(self, include_content=False):
        data = {
            'id': self.id,
            'title': self.title,
            'preview': self.preview or (self.content[:200] + '...' if len(self.content) > 200 else self.content),
            'author': {
                'id': self.author.id if self.author else None,
                'username': self.author.username if self.author else None,
                'avatar_url': self.author.avatar_url if self.author else None
            },
            'like_count': self.like_count,
            'favorite_count': self.favorite_count,
            'comment_count': self.comment_count,
            'tags': [tag.name for tag in self.tags],
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
        
        if include_content:
            data['content'] = self.content
            data['paper_info'] = {
                'title': self.paper_title,
                'authors': self._parse_json(self.paper_authors),
                'journal': self.paper_journal,
                'pub_date': self.paper_pub_date,
                'doi': self.paper_doi,
                'pmid': self.paper_pmid,
                'url': self.paper_url
            }
            data['media_urls'] = self._parse_json(self.media_urls)
        
        return data
    
    def to_detail_dict(self, current_user_id=None):
        data = self.to_dict(include_content=True)
        if current_user_id:
            data['is_liked'] = Like.query.filter_by(
                user_id=current_user_id, note_id=self.id
            ).first() is not None
            data['is_favorited'] = Favorite.query.filter_by(
                user_id=current_user_id, note_id=self.id
            ).first() is not None
        else:
            data['is_liked'] = False
            data['is_favorited'] = False
        return data
    
    def _parse_json(self, text):
        if not text:
            return []
        try:
            import json
            return json.loads(text)
        except:
            return []


class Like(db.Model):
    """点赞模型"""
    __tablename__ = 'likes'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    note_id = db.Column(db.Integer, db.ForeignKey('notes.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    __table_args__ = (db.UniqueConstraint('user_id', 'note_id', name='unique_user_note_like'),)


class Favorite(db.Model):
    """收藏模型"""
    __tablename__ = 'favorites'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    note_id = db.Column(db.Integer, db.ForeignKey('notes.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    __table_args__ = (db.UniqueConstraint('user_id', 'note_id', name='unique_user_note_favorite'),)


class Comment(db.Model):
    """评论模型"""
    __tablename__ = 'comments'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    note_id = db.Column(db.Integer, db.ForeignKey('notes.id'), nullable=False)
    content = db.Column(db.Text, nullable=False)
    parent_id = db.Column(db.Integer, db.ForeignKey('comments.id'))
    like_count = db.Column(db.Integer, default=0)
    is_deleted = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    replies = db.relationship('Comment', backref=db.backref('parent', remote_side=[id]), lazy='dynamic')
    
    def to_dict(self):
        return {
            'id': self.id,
            'content': self.content if not self.is_deleted else '[已删除]',
            'author': {
                'id': self.user.id if self.user else None,
                'username': self.user.username if self.user else None,
                'avatar_url': self.user.avatar_url if self.user else None
            },
            'like_count': self.like_count,
            'parent_id': self.parent_id,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }