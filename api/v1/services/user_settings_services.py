from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from api.v1.models.user.user import User, UserProfile, UserSettings
from api.v1.schemas.user_settings import (
    UserProfileUpdate,
    NotificationPreferencesUpdate,
    AppSettingsUpdate,
    PasswordUpdate
)
from api.utils.security import hash_password, verify_password
from api.utils.logger import logger
from datetime import datetime, time as time_type
from typing import Optional, Tuple
import uuid


def get_user_settings(db: Session, user_id: uuid.UUID) -> Optional[dict]:
    """Get user settings with all profile and app settings data"""
    logger.info("Fetching settings for user_id: %s", user_id)
    
    user = User.fetch_one(
        db,
        id=user_id,
        is_active=True,
        is_deleted=False
    )
    
    if not user:
        logger.warning("User not found or inactive: %s", user_id)
        return None
    
    # Create profile if it doesn't exist
    if not user.profile:
        logger.info("Creating profile for user: %s", user_id)
        profile = UserProfile(user_id=user_id)
        profile.insert(db)
        db.refresh(user)
    
    # Create settings if they don't exist
    if not user.settings:
        logger.info("Creating settings for user: %s", user_id)
        settings = UserSettings(
            user_id=user_id,
            daily_reminder_time=time_type(9, 0, 0)
        )
        settings.insert(db)
        db.refresh(user)
    
    return {
        "id": user.id,
        "full_name": user.full_name,
        "email": user.email,
        "phone": user.phone,
        
        # Profile data
        "date_of_birth": user.profile.date_of_birth,
        "state": user.profile.state,
        "country": user.profile.country,
        "occupation": user.profile.occupation,
        "preferred_language": user.profile.preferred_language,
        "timezone": user.profile.timezone,
        "avatar_url": user.profile.avatar_url,
        "bio": user.profile.bio,
        
        # Notification preferences
        "push_notifications_enabled": user.profile.push_notifications_enabled,
        "email_notifications_enabled": user.profile.email_notifications_enabled,
        "sms_notifications_enabled": user.profile.sms_notifications_enabled,
        
        # App settings
        "dark_mode": user.settings.dark_mode,
        "ai_voice_enabled": user.settings.ai_voice_enabled,
        "daily_reminder_time": user.settings.daily_reminder_time,
        "chat_history_visible": user.settings.chat_history_visible,
        "show_milestone_reminders": user.settings.show_milestone_reminders,
        "community_visibility": user.settings.community_visibility,
    }


def update_user_profile(
    db: Session,
    user_id: uuid.UUID,
    profile_data: UserProfileUpdate
) -> Tuple[Optional[dict], Optional[str]]:
    """Update user profile information"""
    logger.info("Updating profile for user_id: %s", user_id)
    
    user = User.fetch_one(db, id=user_id)
    
    if not user:
        logger.warning("User not found: %s", user_id)
        return None, "User not found"
    
    try:
        # Update user basic info
        if profile_data.full_name is not None:
            user.full_name = profile_data.full_name
        
        if profile_data.email is not None:
            existing = User.fetch_one(db, email=profile_data.email)
            if existing and existing.id != user_id:
                logger.warning("Email already in use: %s", profile_data.email)
                return None, "Email already in use"
            user.email = profile_data.email
        
        if profile_data.phone is not None:
            existing = User.fetch_one(db, phone=profile_data.phone)
            if existing and existing.id != user_id:
                logger.warning("Phone already in use: %s", profile_data.phone)
                return None, "Phone number already in use"
            user.phone = profile_data.phone
        
        user.update(db, commit=False)
        
        # Create profile if it doesn't exist
        if not user.profile:
            logger.info("Creating profile for user: %s", user_id)
            user.profile = UserProfile(user_id=user_id)
            user.profile.insert(db, commit=False)
        
        # Update profile fields
        if profile_data.date_of_birth is not None:
            user.profile.date_of_birth = profile_data.date_of_birth
        if profile_data.state is not None:
            user.profile.state = profile_data.state
        if profile_data.country is not None:
            user.profile.country = profile_data.country
        if profile_data.occupation is not None:
            user.profile.occupation = profile_data.occupation
        if profile_data.preferred_language is not None:
            user.profile.preferred_language = profile_data.preferred_language
        if profile_data.timezone is not None:
            user.profile.timezone = profile_data.timezone
        if profile_data.avatar_url is not None:
            user.profile.avatar_url = profile_data.avatar_url
        if profile_data.bio is not None:
            user.profile.bio = profile_data.bio
        
        user.profile.update(db)
        
        logger.info("Profile updated successfully for user: %s", user_id)
        return get_user_settings(db, user_id), None
        
    except IntegrityError as e:
        db.rollback()
        logger.error("Database integrity error updating profile: %s", str(e), exc_info=True)
        return None, "Database integrity error"
    except Exception as e:
        db.rollback()
        logger.error("Error updating profile: %s", str(e), exc_info=True)
        return None, f"Error updating profile: {str(e)}"


def update_notification_preferences(
    db: Session,
    user_id: uuid.UUID,
    notification_data: NotificationPreferencesUpdate
) -> Tuple[Optional[dict], Optional[str]]:
    """Update user notification preferences"""
    logger.info("Updating notification preferences for user_id: %s", user_id)
    
    user = User.fetch_one(db, id=user_id)
    
    if not user:
        logger.warning("User not found: %s", user_id)
        return None, "User not found"
    
    # Create profile if it doesn't exist
    if not user.profile:
        logger.info("Creating profile for user: %s", user_id)
        user.profile = UserProfile(user_id=user_id)
        user.profile.insert(db, commit=False)
    
    try:
        if notification_data.push_notifications_enabled is not None:
            user.profile.push_notifications_enabled = notification_data.push_notifications_enabled
        if notification_data.email_notifications_enabled is not None:
            user.profile.email_notifications_enabled = notification_data.email_notifications_enabled
        if notification_data.sms_notifications_enabled is not None:
            user.profile.sms_notifications_enabled = notification_data.sms_notifications_enabled
        
        user.profile.update(db)
        
        logger.info("Notification preferences updated successfully for user: %s", user_id)
        return get_user_settings(db, user_id), None
        
    except Exception as e:
        db.rollback()
        logger.error("Error updating notifications: %s", str(e), exc_info=True)
        return None, f"Error updating notifications: {str(e)}"


def update_app_settings(
    db: Session,
    user_id: uuid.UUID,
    settings_data: AppSettingsUpdate
) -> Tuple[Optional[dict], Optional[str]]:
    """Update user app settings"""
    logger.info("Updating app settings for user_id: %s", user_id)
    
    user = User.fetch_one(db, id=user_id)
    
    if not user:
        logger.warning("User not found: %s", user_id)
        return None, "User not found"
    
    # Create settings if they don't exist
    if not user.settings:
        logger.info("Creating settings for user: %s", user_id)
        user.settings = UserSettings(user_id=user_id)
        user.settings.insert(db, commit=False)
    
    try:
        if settings_data.dark_mode is not None:
            user.settings.dark_mode = settings_data.dark_mode
        if settings_data.ai_voice_enabled is not None:
            user.settings.ai_voice_enabled = settings_data.ai_voice_enabled
        if settings_data.daily_reminder_time is not None:
            user.settings.daily_reminder_time = settings_data.daily_reminder_time
        if settings_data.chat_history_visible is not None:
            user.settings.chat_history_visible = settings_data.chat_history_visible
        if settings_data.show_milestone_reminders is not None:
            user.settings.show_milestone_reminders = settings_data.show_milestone_reminders
        if settings_data.community_visibility is not None:
            user.settings.community_visibility = settings_data.community_visibility
        
        user.settings.update(db)
        
        logger.info("App settings updated successfully for user: %s", user_id)
        return get_user_settings(db, user_id), None
        
    except Exception as e:
        db.rollback()
        logger.error("Error updating settings: %s", str(e), exc_info=True)
        return None, f"Error updating settings: {str(e)}"


def update_password(
    db: Session,
    user_id: uuid.UUID,
    password_data: PasswordUpdate
) -> Tuple[bool, Optional[str]]:
    """Update user password with proper security"""
    logger.info("Password update request for user_id: %s", user_id)
    
    user = User.fetch_one(db, id=user_id)
    
    if not user:
        logger.warning("User not found: %s", user_id)
        return False, "User not found"
    
    if not password_data.validate_passwords_match():
        logger.warning("Password mismatch for user: %s", user_id)
        return False, "New password and confirmation do not match"
    
    # Verify current password
    if not user.password_hash:
        logger.warning("User has no password set: %s", user_id)
        return False, "Current password is invalid"
    
    if not verify_password(password_data.current_password, user.password_hash):
        logger.warning("Current password verification failed for user: %s", user_id)
        return False, "Current password is incorrect"
    
    # Hash and update new password
    try:
        user.password_hash = hash_password(password_data.new_password)
        user.update(db)
        
        logger.info("Password updated successfully for user: %s", user_id)
        return True, None
    except Exception as e:
        db.rollback()
        logger.error("Error updating password: %s", str(e), exc_info=True)
        return False, f"Error updating password: {str(e)}"
