from fastapi import APIRouter

from .waitlist import router as waitlist_router
from .register import router as auth_router
from .change_password import change_password_router
from .forgot_password import router as forgot_password_router
from .login import login_router
from .reset_password import reset_router as reset_password_router
from .email_verification import router as email_verification_router
from .verify_otp import router as verify_otp_router
from .delete_account import router as delete_account_router


app = APIRouter()
app.include_router(auth_router)
app.include_router(email_verification_router)
app.include_router(login_router)
app.include_router(change_password_router)
app.include_router(forgot_password_router)
app.include_router(verify_otp_router)
app.include_router(waitlist_router)
app.include_router(reset_password_router)
app.include_router(delete_account_router)




# Backwards-compatibility: some modules (e.g. main.py) import `contact_router`.
# Export the package-level router under that name so existing imports continue to work.
contact_router = app
