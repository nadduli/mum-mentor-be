from fastapi import APIRouter

from .waitlist import router as waitlist_router
from .register import router as register_router
from .auth.login import login_router
from .reset_password import reset_password_router
from .user_profile import router as user_profile_router

app = APIRouter()

app.include_router(login_router)
app.include_router(waitlist_router)
app.include_router(register_router)
app.include_router(reset_password_router)
app.include_router(user_profile_router)

# Backwards compatibility
contact_router = app
