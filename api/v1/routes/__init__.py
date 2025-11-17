from fastapi import APIRouter
from .waitlist import router as waitlist_router

app = APIRouter()
app.include_router(waitlist_router)
