from fastapi import APIRouter
from .get_user_convos import router as get_convos_router
from .send_message import router as send_message_router
from .create_session import router as create_session_router

# Combine all AI chat routers
router = APIRouter()
router.include_router(get_convos_router)
router.include_router(send_message_router)
router.include_router(create_session_router)

__all__ = ["router"]
