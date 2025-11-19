from fastapi import APIRouter

from .waitlist import router as waitlist_router
from .downloads import router as downloads_router
from .refresh_token import router as refresh_token_router
from .register import router as auth_router
from .google_auth import router as google_auth_router
from .change_password import change_password_router
from .forgot_password import router as forgot_password_router
from .login import login_router
from .reset_password import reset_router as reset_password_router
from .email_verification import router as email_verification_router
from .verify_otp import router as verify_otp_router
from .delete_account import router as delete_account_router
from .user_profile import router as user_profile_router
from .admin import router as admin_router
from .faq import router as faq_router



app = APIRouter()
app.include_router(auth_router)
app.include_router(email_verification_router)
app.include_router(login_router)
app.include_router(change_password_router)
app.include_router(forgot_password_router)
app.include_router(verify_otp_router)
app.include_router(waitlist_router)

app.include_router(refresh_token_router)

app.include_router(reset_password_router)
app.include_router(google_auth_router)
app.include_router(change_password_router)
app.include_router(delete_account_router)
app.include_router(user_profile_router)


app.include_router(downloads_router)
app.include_router(admin_router)
app.include_router(faq_router)



# Backwards-compatibility: some modules (e.g. main.py) import `contact_router`.
# Export the package-level router under that name so existing imports continue to work.
contact_router = app
