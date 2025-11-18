from fastapi import APIRouter
from .waitlist import router as waitlist_router
from .register import router as auth_router
from .user_profile import router as user_profile_router


app = APIRouter()
app.include_router(waitlist_router)
app.include_router(auth_router)
app.include_router(user_profile_router)

# Backwards-compatibility: some modules (e.g. main.py) import `contact_router`.
# Export the package-level router under that name so existing imports continue to work.
contact_router = app
