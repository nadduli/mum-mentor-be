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
from .task import router as task_router
from .task_list import router as task_list_router


from .user_settings import router as user_settings_router
from .edit_task import router as edit_task_router
from .task import router as toggle_completion_router
from .delete_task import router as delete_task_router
from .validate_token import router as validate_token_router

app = APIRouter()

# Authentication routes
app.include_router(auth_router)
app.include_router(email_verification_router)
app.include_router(login_router)
app.include_router(change_password_router)
app.include_router(forgot_password_router)
app.include_router(verify_otp_router)
app.include_router(waitlist_router)
app.include_router(reset_password_router)
app.include_router(google_auth_router)
# app.include_router(change_password_router)
app.include_router(delete_account_router)
app.include_router(validate_token_router)
app.include_router(task_router)
app.include_router(task_list_router)


app.include_router(edit_task_router)
app.include_router(toggle_completion_router)
app.include_router(delete_task_router)





# Backwards-compatibility: some modules (e.g. main.py) import `contact_router`.
# Export the package-level router under that name so existing imports continue to work.
contact_router = app
