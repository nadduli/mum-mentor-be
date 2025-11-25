from fastapi import APIRouter, Depends, status, HTTPException
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from api.db.database import get_db
from api.v1.models.user.user import User
from api.v1.schemas.profile_setup import (
    ProfileSetupSubmit,
    ProfileSetupResponse,
    ProfileSetupUpdate,
)
from api.v1.services.profile_setup import ProfileSetupService, ProfileSetupExistsError
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
def create_profile_setup(
    payload: ProfileSetupSubmit,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Create a new profile setup for the authenticated user.
    """

    logger.info(f"Creating profile setup | user_id={current_user.id}")

    try:
        service = ProfileSetupService()

        profile = service.create(
            session=db,
            user_id=current_user.id,
            payload=payload,
        )

        return success_response(
            status_code=status.HTTP_201_CREATED,
            message="Profile setup created successfully",
            data=profile,
        )

    except ProfileSetupExistsError as e:
        logger.info(f"Profile setup already exists for user {current_user.id}")

        return fail_response(
            status_code=status.HTTP_409_CONFLICT,
            message=str(e),
            context={"detail": str(e)},
        )

    except SQLAlchemyError as db_err:
        logger.error(
            f"[DB ERROR] creating profile setup for user {current_user.id}: {db_err}"
        )

        return fail_response(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            message="Database error occurred while creating profile setup",
            context={"error": str(db_err)},
        )

    except Exception as e:
        logger.error(
            f"[UNEXPECTED ERROR] creating profile setup for user {current_user.id}: {e}"
        )

        return fail_response(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            message="An unexpected error occurred",
            context={"error": str(e)},
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
