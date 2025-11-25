from fastapi import APIRouter

from .waitlist import router as waitlist_router
from .downloads import router as downloads_router
from .auth import auth_router
from .auth import google_auth_router
from .delete_account import router as delete_account_router
from .user_profile import router as user_profile_router
from .admin import router as admin_router
from .faq import router as faq_router
from .user_settings import router as user_settings_router

from .task.list_task import router as task_list_router
from .task.create_task import router as create_task_router
from .task.edit_task import router as edit_task_router
from .task.toggle_completion import router as toggle_completion_router
from .task.delete_task import router as delete_task_router

from .chats import chat_router
from .ai_chat import router as ai_chat_router
from .profile_setup import router as profile_setup_router

app = APIRouter()

# Authentication routes
app.include_router(auth_router)
app.include_router(waitlist_router)
app.include_router(google_auth_router)
app.include_router(delete_account_router)

# Task routes 
app.include_router(create_task_router)
app.include_router(task_list_router)
app.include_router(edit_task_router)
app.include_router(toggle_completion_router)
app.include_router(delete_task_router)

# Profile Setup routes
app.include_router(profile_setup_router)

# Chat routes (The Master Router from /chats folder)
app.include_router(chat_router)

# AI Chat routes
app.include_router(ai_chat_router)

# Other routes
app.include_router(user_profile_router)
app.include_router(admin_router)
app.include_router(faq_router)
app.include_router(user_settings_router)

# Backwards-compatibility
contact_router = app