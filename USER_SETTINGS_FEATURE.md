# User Settings Feature - Implementation Guide

## Overview
This feature allows authenticated users to view and update their personal settings, including profile information, notification preferences, and app-specific settings.

## Files Created

### 1. **api/v1/dependencies/auth.py**
- Mock authentication dependency for development
- **TODO**: Replace with real JWT authentication when auth team completes their work
- Currently returns first active user for testing

### 2. **api/v1/schemas/user_settings.py**
- Pydantic schemas for request/response validation
- Includes validation for email, phone, password strength
- Schemas:
  - `UserSettingsResponse` - Complete settings response
  - `UserProfileUpdate` - Update profile info
  - `NotificationPreferencesUpdate` - Update notification settings
  - `AppSettingsUpdate` - Update app settings
  - `PasswordUpdate` - Change password with validation
  - `UserSettingsUpdate` - Combined update schema

### 3. **api/v1/services/user_settings_services.py**
- Business logic layer
- Functions:
  - `get_user_settings()` - Retrieve user settings
  - `update_user_profile()` - Update profile with validation
  - `update_notification_preferences()` - Update notifications
  - `update_app_settings()` - Update app settings
  - `update_password()` - Change password (needs auth team integration)

### 4. **api/v1/routes/user_settings_r.py**
- API endpoints
- All routes require authentication via `get_current_user` dependency

## API Endpoints

### GET /api/v1/user/settings
Get current user's complete settings
- **Auth**: Required
- **Response**: User profile, notifications, and app settings

### PUT /api/v1/user/settings
Update multiple settings at once
- **Auth**: Required
- **Body**: `UserSettingsUpdate` (supports partial updates)
- **Response**: Updated settings

### PUT /api/v1/user/settings/profile
Update profile information only
- **Auth**: Required
- **Body**: `UserProfileUpdate`
- **Fields**: name, email, phone, DOB, location, occupation, language, timezone, avatar, bio

### PUT /api/v1/user/settings/notifications
Update notification preferences only
- **Auth**: Required
- **Body**: `NotificationPreferencesUpdate`
- **Fields**: push, email, SMS notifications

### PUT /api/v1/user/settings/app
Update app settings only
- **Auth**: Required
- **Body**: `AppSettingsUpdate`
- **Fields**: dark_mode, ai_voice, reminders, chat_history, community_visibility

### PUT /api/v1/user/password
Change user password
- **Auth**: Required
- **Body**: `PasswordUpdate`
- **Validation**: Min 8 chars, uppercase, lowercase, digit required

## Testing the Feature

### 1. Create a Test User (if none exists)
```python
# Run this in Python shell or create a migration
from api.db.database import SessionLocal
from api.v1.models.user.user import User
import uuid

db = SessionLocal()
user = User(
    id=uuid.uuid4(),
    full_name="Test User",
    email="test@example.com",
    is_active=True
)
db.add(user)
db.commit()
```

### 2. Test Endpoints

**Get Settings:**
```bash
curl -X GET http://localhost:8000/api/v1/user/settings
```

**Update Profile:**
```bash
curl -X PUT http://localhost:8000/api/v1/user/settings/profile \
  -H "Content-Type: application/json" \
  -d '{
    "full_name": "Updated Name",
    "bio": "New bio"
  }'
```

**Update Notifications:**
```bash
curl -X PUT http://localhost:8000/api/v1/user/settings/notifications \
  -H "Content-Type: application/json" \
  -d '{
    "email_notifications_enabled": false,
    "push_notifications_enabled": true
  }'
```

**Update App Settings:**
```bash
curl -X PUT http://localhost:8000/api/v1/user/settings/app \
  -H "Content-Type: application/json" \
  -d '{
    "dark_mode": true,
    "community_visibility": "private"
  }'
```

**Change Password:**
```bash
curl -X PUT http://localhost:8000/api/v1/user/password \
  -H "Content-Type: application/json" \
  -d '{
    "current_password": "oldpass",
    "new_password": "NewPass123",
    "confirm_password": "NewPass123"
  }'
```

## Integration with Auth Team

### What Needs to be Replaced:

1. **api/v1/dependencies/auth.py**
   - Replace `get_current_user()` function
   - Should extract JWT from Authorization header
   - Should validate token and return authenticated user

2. **api/v1/services/user_settings_services.py**
   - In `update_password()` function:
     - Replace mock password verification with real `verify_password()`
     - Replace mock password hashing with real `hash_password()`

### Expected Auth Interface:
```python
# What auth team should provide:
from api.utils.security import hash_password, verify_password, verify_jwt_token

async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
) -> User:
    payload = verify_jwt_token(token)
    user_id = payload.get("user_id")
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=401, detail="Invalid token")
    return user
```

## Security Features

✅ Input validation with Pydantic
✅ Email uniqueness check
✅ Phone uniqueness check
✅ Password strength validation
✅ Separate password update endpoint
✅ Database transaction handling
✅ Error handling and rollback

## Notes for Team

- All TODO comments mark integration points with auth system
- Mock authentication allows independent development
- Feature is fully functional with mock auth
- Easy to swap mock with real auth (single function replacement)
- All endpoints follow existing project patterns (waitlist route)
- Uses existing response utilities (`success_response`, `fail_response`)

## Running the Application

```bash
# Install dependencies (if not already installed)
pip install -r requirements.txt

# Run the server
python main.py

# Or with uvicorn directly
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

API documentation available at: http://localhost:8000/docs
