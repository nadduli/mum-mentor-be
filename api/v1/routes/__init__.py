from fastapi import APIRouter
from .waitlist import router as waitlist_router
from .user_settings_r import router as user_settings_router

app = APIRouter()
app.include_router(waitlist_router)

# Backwards-compatibility: some modules (e.g. main.py) import `contact_router`.
# Export the package-level router under that name so existing imports continue to work.
contact_router = app
app.include_router(user_settings_router)
