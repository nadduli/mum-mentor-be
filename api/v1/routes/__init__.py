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
from .user_settings import router as user_settings_router
from .validate_token import router as validate_token_router

from .task.list_task import router as task_list_router
from .task.create_task import router as create_task_router
from .task.edit_task import router as edit_task_router
from .task.toggle_completion import router as toggle_completion_router
from .task.delete_task import router as delete_task_router

from .profile_setup.profile_setup import router as profile_setup_router

from .profile_setup.update_profile import router as update_profile_router

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
app.include_router(delete_account_router)
app.include_router(validate_token_router)

# Task routes 
app.include_router(create_task_router)
app.include_router(task_list_router)
app.include_router(edit_task_router)
app.include_router(toggle_completion_router)
app.include_router(delete_task_router)

# Profile Setup routes
app.include_router(profile_setup_router)
app.include_router(update_profile_router, prefix="/profile-setup", tags=["Profile Setup"])

# Other routes
app.include_router(user_profile_router)
app.include_router(admin_router)
app.include_router(faq_router)
app.include_router(user_settings_router)

# Backwards-compatibility
contact_router = app