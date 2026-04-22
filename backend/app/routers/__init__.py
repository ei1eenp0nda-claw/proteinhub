"""
API routers package for ProteinHub.
"""
from app.routers.auth import router as auth_router
from app.routers.proteins import router as proteins_router
from app.routers.favorites import router as favorites_router

__all__ = ["auth_router", "proteins_router", "favorites_router"]