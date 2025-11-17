from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from api.db.database import get_db
from api.v1.dependencies.auth import get_current_user
from api.v1.models.user.user import User
from api.v1.schemas.user_settings import (
    UserSettingsResponse,
    UserSettingsUpdate,
    UserProfileUpdate,
    NotificationPreferencesUpdate,
    AppSettingsUpdate,
    PasswordUpdate
)
from api.v1.services.user_settings_services import (
    get_user_settings,
    update_user_profile,
    update_notification_preferences,
    update_app_settings,
    update_password
)
from api.utils.responses import success_response, fail_response

router = APIRouter(prefix="/user", tags=["User Settings"])


@router.get("/settings", status_code=status.HTTP_200_OK)
async def get_settings(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    settings = get_user_settings(db, current_user.id)
    
    if not settings:
        return fail_response(
            status_code=status.HTTP_404_NOT_FOUND,
            message="User settings not found"
        )
    
    return success_response(
        status_code=status.HTTP_200_OK,
        message="Settings retrieved successfully",
        data=settings
    )


@router.put("/settings", status_code=status.HTTP_200_OK)
async def update_settings(
    settings_update: UserSettingsUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    updated_data = None
    
    if settings_update.profile:
        success, error, data = update_user_profile(
            db, current_user.id, settings_update.profile
        )
        if not success:
            return fail_response(
                status_code=status.HTTP_400_BAD_REQUEST,
                message=error or "Failed to update profile"
            )
        updated_data = data
    
    if settings_update.notifications:
        success, error, data = update_notification_preferences(
            db, current_user.id, settings_update.notifications
        )
        if not success:
            return fail_response(
                status_code=status.HTTP_400_BAD_REQUEST,
                message=error or "Failed to update notification preferences"
            )
        updated_data = data
    
    if settings_update.app_settings:
        success, error, data = update_app_settings(
            db, current_user.id, settings_update.app_settings
        )
        if not success:
            return fail_response(
                status_code=status.HTTP_400_BAD_REQUEST,
                message=error or "Failed to update app settings"
            )
        updated_data = data
    
    if not updated_data:
        updated_data = get_user_settings(db, current_user.id)
    
    return success_response(
        status_code=status.HTTP_200_OK,
        message="Settings updated successfully",
        data=updated_data
    )


@router.put("/settings/profile", status_code=status.HTTP_200_OK)
async def update_profile(
    profile_update: UserProfileUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    success, error, data = update_user_profile(db, current_user.id, profile_update)
    
    if not success:
        return fail_response(
            status_code=status.HTTP_400_BAD_REQUEST,
            message=error or "Failed to update profile"
        )
    
    return success_response(
        status_code=status.HTTP_200_OK,
        message="Profile updated successfully",
        data=data
    )


@router.put("/settings/notifications", status_code=status.HTTP_200_OK)
async def update_notifications(
    notification_update: NotificationPreferencesUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    success, error, data = update_notification_preferences(
        db, current_user.id, notification_update
    )
    
    if not success:
        return fail_response(
            status_code=status.HTTP_400_BAD_REQUEST,
            message=error or "Failed to update notification preferences"
        )
    
    return success_response(
        status_code=status.HTTP_200_OK,
        message="Notification preferences updated successfully",
        data=data
    )


@router.put("/settings/app", status_code=status.HTTP_200_OK)
async def update_app_settings_route(
    app_settings_update: AppSettingsUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    success, error, data = update_app_settings(
        db, current_user.id, app_settings_update
    )
    
    if not success:
        return fail_response(
            status_code=status.HTTP_400_BAD_REQUEST,
            message=error or "Failed to update app settings"
        )
    
    return success_response(
        status_code=status.HTTP_200_OK,
        message="App settings updated successfully",
        data=data
    )


@router.put("/password", status_code=status.HTTP_200_OK)
async def change_password(
    password_update: PasswordUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    success, error = update_password(db, current_user.id, password_update)
    
    if not success:
        return fail_response(
            status_code=status.HTTP_400_BAD_REQUEST,
            message=error or "Failed to update password"
        )
    
    return success_response(
        status_code=status.HTTP_200_OK,
        message="Password updated successfully",
        data={"password_changed": True}
    )
