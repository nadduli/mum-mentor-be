from fastapi import APIRouter
from .waitlist import router as waitlist_router
from .register import router as auth_router
from .google_auth import router as google_auth_router
from .reset_password import router as reset_password_router
app = APIRouter()
app.include_router(waitlist_router)
app.include_router(auth_router)
app.include_router(reset_password_router)
app.include_router(google_auth_router)
# Backwards-compatibility: some modules (e.g. main.py) import `contact_router`.
# Export the package-level router under that name so existing imports continue to work.
contact_router = app

