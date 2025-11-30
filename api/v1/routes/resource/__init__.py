"""
This module initializes the resource router.
"""

from fastapi import APIRouter
from .routes import resource_router as resource_routes

resource_router = APIRouter()
resource_router.include_router(resource_routes)

__all__ = ["resource_router"]
