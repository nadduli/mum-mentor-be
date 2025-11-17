from fastapi import APIRouter
from .waitlist import router as waitlist_router
from .reset_password import router as reset_password_router

app = APIRouter()
app.include_router(waitlist_router)
app.include_router(reset_password_router)
