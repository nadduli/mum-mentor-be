from fastapi import APIRouter

from .routes import album_router

router = APIRouter(prefix="/album", tags=["Albums"])
router.include_router(album_router)

__all__ = ["router"]