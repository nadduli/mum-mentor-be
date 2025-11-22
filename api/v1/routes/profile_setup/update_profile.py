from fastapi import APIRouter, Depends, status, HTTPException
from sqlalchemy.orm import Session

from api.db.database import get_db
from api.v1.dependencies.auth import get_current_user
from api.utils.responses import success_response, fail_response
from api.v1.schemas.profile_setup.update_profile import ProfileSetupUpdate
from api.v1.services.profile_setup.update_profile import ProfileUpdateService

router = APIRouter()

@router.patch("/", status_code=status.HTTP_200_OK)
def update_profile_setup(
    payload: ProfileSetupUpdate,
    session: Session = Depends(get_db),
    current_user = Depends(get_current_user),
):
    """
    Partially update the user's profile setup.
    Only fields provided in the request body will be updated.
    """
    try:
        updated_profile = ProfileUpdateService.update(
            session=session,
            user_id=current_user.id,
            payload=payload
        )

        return success_response(
            status_code=status.HTTP_200_OK,
            message="Profile updated successfully",
            data={
                "user_id": str(updated_profile.user_id),
                "mom_status": updated_profile.mom_status,
                "goals": updated_profile.goals,
                "partner": updated_profile.partner,
                "children": [
                    {
                        "full_name": c.full_name,
                        "gender": c.gender,
                        "date_of_birth": c.date_of_birth
                    } for c in updated_profile.children
                ]
            }
        )
    except HTTPException as e:
        return fail_response(
            status_code=e.status_code,
            message=e.detail,
            context={"detail": e.detail}
        )

    except Exception as e:
        return fail_response(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            message="Failed to update profile",
            context={"detail": str(e)}
        )