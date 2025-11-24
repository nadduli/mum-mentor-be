from fastapi import APIRouter
from .delete_chat import router as delete_chat_router

chat_router = APIRouter(prefix="/chat", tags=["Chat"])

chat_router.include_router(delete_chat_router)