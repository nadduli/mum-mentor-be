"""
Journal module initialization.
"""

from fastapi import APIRouter
from .routes import router as journal_routes

journal_router = APIRouter()
journal_router.include_router(journal_routes)

__all__ = ["journal_router"]
