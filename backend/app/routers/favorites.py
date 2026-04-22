"""
Favorites routes for managing user favorite proteins.
"""
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import and_

from app.database import get_db
from app.auth.security import get_current_active_user
from app.schemas import UserFavoriteResponse, ProteinResponse
from app.models import User, Protein, UserFavorite

router = APIRouter(prefix="/favorites", tags=["favorites"])


def protein_to_response(protein: Protein, user_favorite_ids: set) -> ProteinResponse:
    """Convert protein to response with favorite info."""
    return ProteinResponse(
        id=protein.id,
        name=protein.name,
        sequence=protein.sequence,
        description=protein.description,
        molecular_weight=protein.molecular_weight,
        species=protein.species,
        function=protein.function,
        created_at=protein.created_at,
        is_favorite=protein.id in user_favorite_ids,
        favorite_count=getattr(protein, 'favorite_count', 0)
    )


@router.get("/", response_model=List[ProteinResponse])
async def get_favorites(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Get all favorite proteins for the current user.
    
    Requires authentication.
    """
    # Get user's favorite proteins
    favorites = (
        db.query(Protein)
        .join(UserFavorite, Protein.id == UserFavorite.protein_id)
        .filter(UserFavorite.user_id == current_user.id)
        .all()
    )
    
    # Get set of favorite protein IDs for this user
    user_favorite_ids = {f.id for f in favorites}
    
    # Convert to response
    return [protein_to_response(protein, user_favorite_ids) for protein in favorites]


@router.post("/{protein_id}", response_model=ProteinResponse, status_code=status.HTTP_201_CREATED)
async def add_favorite(
    protein_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Add a protein to user's favorites.
    
    - **protein_id**: ID of the protein to favorite
    
    Requires authentication.
    """
    # Check if protein exists
    protein = db.query(Protein).filter(Protein.id == protein_id).first()
    if not protein:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Protein not found"
        )
    
    # Check if already favorited
    existing_favorite = (
        db.query(UserFavorite)
        .filter(
            and_(
                UserFavorite.user_id == current_user.id,
                UserFavorite.protein_id == protein_id
            )
        )
        .first()
    )
    
    if existing_favorite:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Protein already in favorites"
        )
    
    # Add to favorites
    new_favorite = UserFavorite(
        user_id=current_user.id,
        protein_id=protein_id
    )
    db.add(new_favorite)
    db.commit()
    
    # Get updated protein with favorite info
    user_favorite_ids = {protein_id}
    return protein_to_response(protein, user_favorite_ids)


@router.delete("/{protein_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_favorite(
    protein_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Remove a protein from user's favorites.
    
    - **protein_id**: ID of the protein to unfavorite
    
    Requires authentication.
    """
    # Check if protein exists
    protein = db.query(Protein).filter(Protein.id == protein_id).first()
    if not protein:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Protein not found"
        )
    
    # Find the favorite
    favorite = (
        db.query(UserFavorite)
        .filter(
            and_(
                UserFavorite.user_id == current_user.id,
                UserFavorite.protein_id == protein_id
            )
        )
        .first()
    )
    
    if not favorite:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Protein not in favorites"
        )
    
    # Remove from favorites
    db.delete(favorite)
    db.commit()
    
    return None