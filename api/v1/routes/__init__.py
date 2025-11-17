from fastapi import APIRouter
from .waitlist import router as waitlist_router
from .downloads import router as downloads_router

app = APIRouter()
app.include_router(waitlist_router)
app.include_router(downloads_router)
