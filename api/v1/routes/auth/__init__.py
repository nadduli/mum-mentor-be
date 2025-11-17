from fastapi import APIRouter
from .refresh_token import router as refresh_token_router

app = APIRouter()
app.include_router(refresh_token_router)