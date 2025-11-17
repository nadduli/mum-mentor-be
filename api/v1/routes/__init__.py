from fastapi import APIRouter
from .waitlist import router as waitlist_router

app = APIRouter()
app.include_router(waitlist_router)

# Backwards-compatibility: some modules (e.g. main.py) import `contact_router`.
# Export the package-level router under that name so existing imports continue to work.
contact_router = app
