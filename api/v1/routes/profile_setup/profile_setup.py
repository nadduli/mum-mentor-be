from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from api.db.database import get_db
from api.v1.schemas.profile_setup.profile_setup import ProfileSetupSubmit
from api.v1.services.profile_setup.profile_setup import ProfileSetupService
from api.v1.dependencies.auth import get_current_user
from api.utils.responses import success_response, fail_response

router = APIRouter(prefix="/profile-setup", tags=["Profile Setup"])


@router.post("/", status_code=status.HTTP_201_CREATED)
def submit_profile_setup(
    payload: ProfileSetupSubmit,
    session: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """
    Create or update (overwrite) the user's profile setup.
    """

    try:
        profile = ProfileSetupService.submit(
            session=session,
            user_id=current_user.id,
            payload=payload,
        )

        return success_response(
            status_code=status.HTTP_201_CREATED,
            message="Profile setup created/updated successfully",
            data=profile,
        )

    except ValueError as ve:
        # Schema / logical validation issues
        return fail_response(
            status_code=status.HTTP_400_BAD_REQUEST,
            message=str(ve),
            context={"detail": str(ve)},
        )

    except Exception as e:
        # Unexpected server errors
        return fail_response(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            message="An unexpected error occurred",
            context={"detail": str(e)},
        )