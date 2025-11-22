from fastapi import APIRouter
from .profile_setup import router as create_router
from .update_profile import router as update_router

router = APIRouter(prefix="/profile-setup", tags=["Profile Setup"])

router.include_router(create_router) 
router.include_router(update_router)