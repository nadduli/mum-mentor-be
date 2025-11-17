from fastapi import APIRouter
from .waitlist import router as waitlist_router
from .auth.auth import router as auth_router

app = APIRouter()
app.include_router(waitlist_router)
app.include_router(auth_router)