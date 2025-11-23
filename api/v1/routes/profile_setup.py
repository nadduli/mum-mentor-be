from fastapi import APIRouter, Depends, status, HTTPException
from sqlalchemy.orm import Session

from api.db.database import get_db
from api.v1.schemas.profile_setup import (
    ProfileSetupSubmit,
    ProfileSetupResponse,
    ProfileSetupUpdate,
)
from api.v1.services.profile_setup import ProfileSetupService
from api.utils.deps import get_current_user
from api.utils.responses import success_response, fail_response
from api.utils.logger import logger

router = APIRouter(prefix="/profile-setup", tags=["Profile Setup"])

@router.get("/", status_code=status.HTTP_200_OK)
def get_profile_setup(
    session: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """
    Get the current user's profile setup details.
    """
    logger.info(f"Get profile setup request by {current_user.id}")

    profile = ProfileSetupService.get(session, current_user.id)

    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Profile setup not found"
        )
    return success_response(
        status_code=status.HTTP_200_OK,
        message="Profile setup retrieved successfully",
        data=profile,
    )


@router.post("/", status_code=status.HTTP_201_CREATED)
def submit_profile_setup(
    payload: ProfileSetupSubmit,
    session: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """
    Create or update (overwrite) the user's profile setup.
    """

    logger.info(f"Submit profile setup request by {current_user.id}")

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


@router.patch("/", status_code=status.HTTP_200_OK, response_model=ProfileSetupResponse)
def update_profile_setup(
    payload: ProfileSetupUpdate,
    session: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """
    Partially update the user's profile setup.
    Only fields provided in the request body will be updated.
    """
    try:
        updated_profile = ProfileSetupService.update(
            session=session, user_id=current_user.id, payload=payload
        )

        return success_response(
            status_code=status.HTTP_200_OK,
            message="Profile updated successfully",
            data=ProfileSetupService.build_profile(session, updated_profile),
        )
    except HTTPException as e:
        return fail_response(
            status_code=e.status_code, message=e.detail, context={"detail": e.detail}
        )

    except Exception as e:
        return fail_response(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            message="Failed to update profile",
            context={"detail": str(e)},
        )
