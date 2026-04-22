"""
Pydantic schemas for request/response validation.
"""
from app.schemas.schemas import (
    # User schemas
    UserBase, UserCreate, UserUpdate, UserInDB, UserResponse, UserWithFavorites,
    # Protein schemas
    ProteinBase, ProteinCreate, ProteinUpdate, ProteinInDB, ProteinResponse,
    # Favorite schemas
    UserFavoriteBase, UserFavoriteCreate, UserFavoriteInDB, UserFavoriteResponse,
    # Auth schemas
    Token, TokenData, LoginRequest,
    # Pagination schemas
    PaginationParams, PaginatedResponse, ProteinListResponse, UserListResponse,
)

__all__ = [
    # User schemas
    "UserBase", "UserCreate", "UserUpdate", "UserInDB", "UserResponse", "UserWithFavorites",
    # Protein schemas
    "ProteinBase", "ProteinCreate", "ProteinUpdate", "ProteinInDB", "ProteinResponse",
    # Favorite schemas
    "UserFavoriteBase", "UserFavoriteCreate", "UserFavoriteInDB", "UserFavoriteResponse",
    # Auth schemas
    "Token", "TokenData", "LoginRequest",
    # Pagination schemas
    "PaginationParams", "PaginatedResponse", "ProteinListResponse", "UserListResponse",
]