from pydantic import BaseModel, EmailStr, field_validator, Field
from typing import Optional
from datetime import datetime, time
import uuid


class UserSettingsResponse(BaseModel):
    # User basic info
    id: uuid.UUID
    full_name: str
    email: Optional[str]
    phone: Optional[str]
    
    # Profile info
    date_of_birth: Optional[datetime]
    state: Optional[str]
    country: str
    occupation: Optional[str]
    preferred_language: str
    timezone: str
    avatar_url: Optional[str]
    bio: Optional[str]
    
    # Notification preferences
    push_notifications_enabled: bool
    email_notifications_enabled: bool
    sms_notifications_enabled: bool
    
    # App settings
    dark_mode: bool
    ai_voice_enabled: bool
    daily_reminder_time: time
    chat_history_visible: bool
    show_milestone_reminders: bool
    community_visibility: str
    
    model_config = {"from_attributes": True}


class UserProfileUpdate(BaseModel):
    
    full_name: Optional[str] = Field(None, min_length=1, max_length=100)
    email: Optional[EmailStr] = None
    phone: Optional[str] = Field(None, max_length=20)
    
    date_of_birth: Optional[datetime] = None
    state: Optional[str] = Field(None, max_length=100)
    country: Optional[str] = Field(None, max_length=100)
    occupation: Optional[str] = Field(None, max_length=200)
    
    preferred_language: Optional[str] = Field(None, max_length=50)
    timezone: Optional[str] = Field(None, max_length=50)
    avatar_url: Optional[str] = None
    bio: Optional[str] = None
    
    @field_validator("full_name")
    @classmethod
    def validate_full_name(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            v = v.strip()
            if not v:
                raise ValueError("Full name cannot be empty")
        return v
    
    @field_validator("email")
    @classmethod
    def normalize_email(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            return v.strip().lower()
        return v
    
    @field_validator("phone")
    @classmethod
    def validate_phone(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            v = v.strip()
            if v and not v.replace("+", "").replace("-", "").replace(" ", "").isdigit():
                raise ValueError("Phone number must contain only digits, +, -, and spaces")
        return v


class NotificationPreferencesUpdate(BaseModel):
    
    push_notifications_enabled: Optional[bool] = None
    email_notifications_enabled: Optional[bool] = None
    sms_notifications_enabled: Optional[bool] = None


class AppSettingsUpdate(BaseModel):
    
    dark_mode: Optional[bool] = None
    ai_voice_enabled: Optional[bool] = None
    daily_reminder_time: Optional[time] = None
    chat_history_visible: Optional[bool] = None
    show_milestone_reminders: Optional[bool] = None
    community_visibility: Optional[str] = Field(None, pattern="^(public|private|friends)$")
    
    @field_validator("community_visibility")
    @classmethod
    def validate_visibility(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and v not in ["public", "private", "friends"]:
            raise ValueError("Community visibility must be 'public', 'private', or 'friends'")
        return v


class PasswordUpdate(BaseModel):
    
    current_password: str = Field(..., min_length=1)
    new_password: str = Field(..., min_length=8, max_length=100)
    confirm_password: str = Field(..., min_length=8, max_length=100)
    
    @field_validator("new_password")
    @classmethod
    def validate_password_strength(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters long")
        
        has_upper = any(c.isupper() for c in v)
        has_lower = any(c.islower() for c in v)
        has_digit = any(c.isdigit() for c in v)
        
        if not (has_upper and has_lower and has_digit):
            raise ValueError(
                "Password must contain at least one uppercase letter, "
                "one lowercase letter, and one digit"
            )
        
        return v
    
    def validate_passwords_match(self) -> bool:
        return self.new_password == self.confirm_password


class UserSettingsUpdate(BaseModel):
    
    profile: Optional[UserProfileUpdate] = None
    notifications: Optional[NotificationPreferencesUpdate] = None
    app_settings: Optional[AppSettingsUpdate] = None
