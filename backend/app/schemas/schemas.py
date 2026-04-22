"""
Pydantic schemas for request/response validation.
"""
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, EmailStr, Field, ConfigDict


# ==================== User Schemas ====================

class UserBase(BaseModel):
    """Base user schema with common attributes."""
    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr


class UserCreate(UserBase):
    """Schema for user registration."""
    password: str = Field(..., min_length=6, max_length=100)


class UserUpdate(BaseModel):
    """Schema for user update."""
    username: Optional[str] = Field(None, min_length=3, max_length=50)
    email: Optional[EmailStr] = None
    password: Optional[str] = Field(None, min_length=6, max_length=100)


class UserInDB(UserBase):
    """Schema for user stored in database."""
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    role: str
    created_at: datetime


class UserResponse(UserInDB):
    """Schema for user response (public)."""
    pass


class UserWithFavorites(UserResponse):
    """Schema for user with favorite proteins."""
    favorites: List["ProteinResponse"] = []


# ==================== Protein Schemas ====================

class ProteinBase(BaseModel):
    """Base protein schema with common attributes."""
    name: str = Field(..., min_length=1, max_length=100)
    sequence: str = Field(..., min_length=1)
    description: Optional[str] = None
    molecular_weight: Optional[float] = Field(None, gt=0)
    species: Optional[str] = Field(None, max_length=100)
    function: Optional[str] = None


class ProteinCreate(ProteinBase):
    """Schema for creating a new protein."""
    pass


class ProteinUpdate(BaseModel):
    """Schema for updating a protein."""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    sequence: Optional[str] = Field(None, min_length=1)
    description: Optional[str] = None
    molecular_weight: Optional[float] = Field(None, gt=0)
    species: Optional[str] = Field(None, max_length=100)
    function: Optional[str] = None


class ProteinInDB(ProteinBase):
    """Schema for protein stored in database."""
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    created_at: datetime


class ProteinResponse(ProteinInDB):
    """Schema for protein response."""
    is_favorite: bool = False
    favorite_count: int = 0


# ==================== Favorite Schemas ====================

class UserFavoriteBase(BaseModel):
    """Base favorite schema."""
    pass


class UserFavoriteCreate(BaseModel):
    """Schema for creating a favorite."""
    protein_id: int


class UserFavoriteInDB(UserFavoriteBase):
    """Schema for favorite stored in database."""
    model_config = ConfigDict(from_attributes=True)
    
    user_id: int
    protein_id: int
    created_at: datetime


class UserFavoriteResponse(UserFavoriteInDB):
    """Schema for favorite response."""
    protein: Optional[ProteinResponse] = None


# ==================== Auth Schemas ====================

class Token(BaseModel):
    """Schema for token response."""
    access_token: str
    token_type: str = "bearer"
    expires_in: int


class TokenData(BaseModel):
    """Schema for token payload."""
    username: Optional[str] = None


class LoginRequest(BaseModel):
    """Schema for login request."""
    username: str
    password: str


# ==================== Pagination Schemas ====================

class PaginationParams(BaseModel):
    """Schema for pagination parameters."""
    page: int = Field(1, ge=1)
    page_size: int = Field(20, ge=1, le=100)


class PaginatedResponse(BaseModel):
    """Base schema for paginated responses."""
    total: int
    page: int
    page_size: int
    total_pages: int


class ProteinListResponse(PaginatedResponse):
    """Schema for paginated protein list."""
    items: List[ProteinResponse]


class UserListResponse(PaginatedResponse):
    """Schema for paginated user list."""
    items: List[UserResponse]