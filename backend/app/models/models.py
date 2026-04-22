"""
SQLAlchemy models for ProteinHub database.
"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Table, Text
from sqlalchemy.orm import relationship

from app.database import Base


class User(Base):
    """User model for authentication and user management."""
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    email = Column(String(100), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    role = Column(String(20), default="user")  # user, admin
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    favorites = relationship("UserFavorite", back_populates="user", cascade="all, delete-orphan")
    favorite_proteins = relationship(
        "Protein",
        secondary="user_favorites",
        back_populates="favorited_by",
        viewonly=True
    )
    
    def __repr__(self):
        return f"<User(id={self.id}, username='{self.username}', email='{self.email}')>"


class Protein(Base):
    """Protein model for storing protein data."""
    __tablename__ = "proteins"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False, index=True)
    sequence = Column(Text, nullable=False)
    description = Column(Text)
    molecular_weight = Column(Float)
    species = Column(String(100), index=True)
    function = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    favorited_by = relationship(
        "User",
        secondary="user_favorites",
        back_populates="favorite_proteins",
        viewonly=True
    )
    favorites = relationship("UserFavorite", back_populates="protein", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Protein(id={self.id}, name='{self.name}', species='{self.species}')>"


class UserFavorite(Base):
    """Association table for user favorites (many-to-many relationship)."""
    __tablename__ = "user_favorites"
    
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    protein_id = Column(Integer, ForeignKey("proteins.id", ondelete="CASCADE"), primary_key=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="favorites")
    protein = relationship("Protein", back_populates="favorites")
    
    def __repr__(self):
        return f"<UserFavorite(user_id={self.user_id}, protein_id={self.protein_id})>"