"""
Protein routes for CRUD operations and search.
"""
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import or_, func

from app.database import get_db
from app.auth.security import get_current_active_user, get_current_user
from app.schemas import (
    ProteinResponse, ProteinListResponse, PaginationParams
)
from app.models import Protein, User, UserFavorite
from app.config import DEFAULT_PAGE_SIZE, MAX_PAGE_SIZE

router = APIRouter(prefix="/proteins", tags=["proteins"])


def get_protein_with_favorite_info(
    protein: Protein,
    current_user: Optional[User] = None,
    db: Session = None
) -> ProteinResponse:
    """
    Convert a Protein model to ProteinResponse with favorite information.
    """
    # Calculate favorite count
    favorite_count = db.query(func.count(UserFavorite.protein_id)).filter(
        UserFavorite.protein_id == protein.id
    ).scalar() or 0
    
    # Check if current user has favorited this protein
    is_favorite = False
    if current_user:
        is_favorite = db.query(UserFavorite).filter(
            UserFavorite.user_id == current_user.id,
            UserFavorite.protein_id == protein.id
        ).first() is not None
    
    # Create response
    response_data = {
        "id": protein.id,
        "name": protein.name,
        "sequence": protein.sequence,
        "description": protein.description,
        "molecular_weight": protein.molecular_weight,
        "species": protein.species,
        "function": protein.function,
        "created_at": protein.created_at,
        "is_favorite": is_favorite,
        "favorite_count": favorite_count
    }
    
    return ProteinResponse(**response_data)


@router.get("/", response_model=ProteinListResponse)
async def list_proteins(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(DEFAULT_PAGE_SIZE, ge=1, le=MAX_PAGE_SIZE, description="Items per page"),
    species: Optional[str] = Query(None, description="Filter by species"),
    search: Optional[str] = Query(None, description="Search in name and description"),
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user)
):
    """
    Get a paginated list of proteins.
    
    - **page**: Page number (default: 1)
    - **page_size**: Number of items per page (default: 20, max: 100)
    - **species**: Filter by species name
    - **search**: Search in protein names and descriptions
    """
    # Build query
    query = db.query(Protein)
    
    # Apply filters
    if species:
        query = query.filter(Protein.species.ilike(f"%{species}%"))
    
    if search:
        search_filter = or_(
            Protein.name.ilike(f"%{search}%"),
            Protein.description.ilike(f"%{search}%")
        )
        query = query.filter(search_filter)
    
    # Get total count
    total = query.count()
    
    # Apply pagination
    offset = (page - 1) * page_size
    proteins = query.offset(offset).limit(page_size).all()
    
    # Convert to response with favorite info
    items = [get_protein_with_favorite_info(p, current_user, db) for p in proteins]
    
    # Calculate total pages
    total_pages = (total + page_size - 1) // page_size
    
    return ProteinListResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages
    )


@router.get("/search", response_model=ProteinListResponse)
async def search_proteins(
    q: str = Query(..., min_length=1, description="Search query"),
    page: int = Query(1, ge=1),
    page_size: int = Query(DEFAULT_PAGE_SIZE, ge=1, le=MAX_PAGE_SIZE),
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user)
):
    """
    Search proteins by name, description, or function.
    
    - **q**: Search query string
    - **page**: Page number
    - **page_size**: Items per page
    """
    # Build search query
    search_filter = or_(
        Protein.name.ilike(f"%{q}%"),
        Protein.description.ilike(f"%{q}%"),
        Protein.function.ilike(f"%{q}%"),
        Protein.species.ilike(f"%{q}%")
    )
    
    query = db.query(Protein).filter(search_filter)
    
    # Get total count
    total = query.count()
    
    # Apply pagination
    offset = (page - 1) * page_size
    proteins = query.offset(offset).limit(page_size).all()
    
    # Convert to response with favorite info
    items = [get_protein_with_favorite_info(p, current_user, db) for p in proteins]
    
    # Calculate total pages
    total_pages = (total + page_size - 1) // page_size
    
    return ProteinListResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages
    )


@router.get("/{protein_id}", response_model=ProteinResponse)
async def get_protein(
    protein_id: int,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user)
):
    """
    Get detailed information about a specific protein.
    
    - **protein_id**: ID of the protein
    """
    protein = db.query(Protein).filter(Protein.id == protein_id).first()
    
    if not protein:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Protein not found"
        )
    
    return get_protein_with_favorite_info(protein, current_user, db)