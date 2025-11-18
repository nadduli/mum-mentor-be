from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from api.db.database import get_db
from api.v1.models.user.user import User, UserProfile
from api.utils.deps import get_current_user

router = APIRouter(
    prefix="/auth",
    tags=["Auth"]
)

@router.get("/profile")
def get_user_profile(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Fetch profile (may be None)
    profile = (
        db.query(UserProfile)
        .filter(UserProfile.user_id == current_user.id)
        .first()
    )

    return {
        "id": str(current_user.id),
        "full_name": current_user.full_name,
        "email": current_user.email,
        "email_verified": current_user.email_verified,
        "phone": current_user.phone,
        "phone_verified": current_user.phone_verified,
        "role": current_user.role,
        "is_active": current_user.is_active,
        "last_login_at": current_user.last_login_at,

        "profile": {
            "date_of_birth": profile.date_of_birth if profile else None,
            "state": profile.state if profile else None,
            "country": profile.country if profile else None,
            "occupation": profile.occupation if profile else None,
            "tech_savviness": profile.tech_savviness if profile else None,
            "preferred_language": profile.preferred_language if profile else None,
            "ai_tone_preference": profile.ai_tone_preference if profile else None,
            "onboarding_stage": profile.onboarding_stage if profile else None,
            "onboarding_completed": profile.onboarding_completed if profile else None,
            "onboarding_completed_at": profile.onboarding_completed_at if profile else None,
            "push_notifications_enabled": profile.push_notifications_enabled if profile else None,
            "email_notifications_enabled": profile.email_notifications_enabled if profile else None,
            "sms_notifications_enabled": profile.sms_notifications_enabled if profile else None,
            "timezone": profile.timezone if profile else None,
            "avatar_url": profile.avatar_url if profile else None,
            "bio": profile.bio if profile else None,
        }
    }
