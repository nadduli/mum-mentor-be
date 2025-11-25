from fastapi import APIRouter
from .new_chat import chat_router as new_chat_router

chat_router = APIRouter(prefix="/chat", tags=["Chat"])

chat_router.include_router(new_chat_router)

__all__ = ["chat_router"]