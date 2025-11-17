from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from api.v1.models.user.user import User, UserProfile, UserSettings
from api.v1.schemas.user_settings import (
    UserProfileUpdate,
    NotificationPreferencesUpdate,
    AppSettingsUpdate,
    PasswordUpdate
)
from datetime import datetime, time as time_type
from typing import Optional, Tuple
import uuid


def get_user_settings(db: Session, user_id: uuid.UUID) -> Optional[dict]:
    user = db.query(User).filter(
        User.id == user_id,
        User.is_active == True,
        User.is_deleted == False
    ).first()
    
    if not user:
        return None
    
    if not user.profile:
        profile = UserProfile(user_id=user_id)
        db.add(profile)
        db.commit()
        db.refresh(user)
    
    if not user.settings:
        settings = UserSettings(
            user_id=user_id,
            daily_reminder_time=time_type(9, 0, 0)
        )
        db.add(settings)
        db.commit()
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
) -> Tuple[bool, Optional[str], Optional[dict]]:
    user = db.query(User).filter(User.id == user_id).first()
    
    if not user:
        return False, "User not found", None
    
    try:
        if profile_data.full_name is not None:
            user.full_name = profile_data.full_name
        
        if profile_data.email is not None:
            existing = db.query(User).filter(
                User.email == profile_data.email,
                User.id != user_id
            ).first()
            if existing:
                return False, "Email already in use", None
            user.email = profile_data.email
        
        if profile_data.phone is not None:
            existing = db.query(User).filter(
                User.phone == profile_data.phone,
                User.id != user_id
            ).first()
            if existing:
                return False, "Phone number already in use", None
            user.phone = profile_data.phone
        
        user.updated_at = datetime.utcnow()
        
        if not user.profile:
            user.profile = UserProfile(user_id=user_id)
        
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
        
        user.profile.updated_at = datetime.utcnow()
        
        db.commit()
        db.refresh(user)
        
        return True, None, get_user_settings(db, user_id)
        
    except IntegrityError as e:
        db.rollback()
        return False, "Database integrity error", None
    except Exception as e:
        db.rollback()
        return False, f"Error updating profile: {str(e)}", None


def update_notification_preferences(
    db: Session,
    user_id: uuid.UUID,
    notification_data: NotificationPreferencesUpdate
) -> Tuple[bool, Optional[str], Optional[dict]]:
    user = db.query(User).filter(User.id == user_id).first()
    
    if not user:
        return False, "User not found", None
    
    if not user.profile:
        user.profile = UserProfile(user_id=user_id)
    
    try:
        if notification_data.push_notifications_enabled is not None:
            user.profile.push_notifications_enabled = notification_data.push_notifications_enabled
        if notification_data.email_notifications_enabled is not None:
            user.profile.email_notifications_enabled = notification_data.email_notifications_enabled
        if notification_data.sms_notifications_enabled is not None:
            user.profile.sms_notifications_enabled = notification_data.sms_notifications_enabled
        
        user.profile.updated_at = datetime.utcnow()
        
        db.commit()
        db.refresh(user)
        
        return True, None, get_user_settings(db, user_id)
        
    except Exception as e:
        db.rollback()
        return False, f"Error updating notifications: {str(e)}", None


def update_app_settings(
    db: Session,
    user_id: uuid.UUID,
    settings_data: AppSettingsUpdate
) -> Tuple[bool, Optional[str], Optional[dict]]:
    user = db.query(User).filter(User.id == user_id).first()
    
    if not user:
        return False, "User not found", None
    
    if not user.settings:
        user.settings = UserSettings(user_id=user_id)
    
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
        
        user.settings.updated_at = datetime.utcnow()
        
        db.commit()
        db.refresh(user)
        
        return True, None, get_user_settings(db, user_id)
        
    except Exception as e:
        db.rollback()
        return False, f"Error updating settings: {str(e)}", None


def update_password(
    db: Session,
    user_id: uuid.UUID,
    password_data: PasswordUpdate
) -> Tuple[bool, Optional[str]]:
    """TODO: Integrate with auth team's password hashing utilities"""
    user = db.query(User).filter(User.id == user_id).first()
    
    if not user:
        return False, "User not found"
    
    if not password_data.validate_passwords_match():
        return False, "New password and confirmation do not match"
    
    # TODO: Replace with real password verification from auth team
    # Example: verify_password(password_data.current_password, user.password_hash)
    # For now, skip current password verification in mock mode
    
    # TODO: Replace with real password hashing from auth team
    # Example: user.password_hash = hash_password(password_data.new_password)
    # For now, store plain text (INSECURE - only for development)
    user.password_hash = f"MOCK_HASH_{password_data.new_password}"
    
    user.updated_at = datetime.utcnow()
    
    try:
        db.commit()
        return True, None
    except Exception as e:
        db.rollback()
        return False, f"Error updating password: {str(e)}"
