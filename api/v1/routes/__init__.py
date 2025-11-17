from fastapi import APIRouter
from .waitlist import router as waitlist_router
from .user_settings_r import router as user_settings_router

app = APIRouter()
app.include_router(waitlist_router)
app.include_router(user_settings_router)
