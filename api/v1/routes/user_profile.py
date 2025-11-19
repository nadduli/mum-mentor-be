from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from api.db.database import get_db
from api.utils.deps import get_current_user
from api.v1.models.user.user import User, UserProfile
from api.utils.responses import success_response
from api.utils.logger import logger


router = APIRouter(
    prefix="/auth",
    tags=["Authentication"]
)


@router.get("/profile")
def get_user_profile(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
   
    Retrieve the authenticated user's profile information.

    This endpoint returns the complete user account details along with their
    associated profile data. It can only be accessed by a logged-in user.

    How it works:
    - The client must include a valid Bearer access token in the Authorization header.
    - The token is decoded using get_current_user, which identifies the logged-in user.
    - The endpoint then fetches both the user record and any additional profile information.

    How to test in Swagger:
    1. Click the Authorize button at the top of Swagger.
    2. Paste your access token in this format:  
       Bearer <your_token_here>
    3. Execute the /auth/profile endpoint.
    """

    logger.info(f"Fetching profile for user_id={current_user.id}")

    # Fetch extended profile using BaseModel CRUD instead of raw query
    profile = UserProfile.fetch_one(db, user_id=current_user.id)

    # Build response data
    profile_data = {
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
        },
    }

    logger.info(f"Successfully fetched profile for user_id={current_user.id}")

    return success_response(
        status_code=status.HTTP_200_OK,
        message="User profile fetched successfully",
        data=profile_data
    )
