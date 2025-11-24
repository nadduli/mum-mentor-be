from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from api.db.database import get_db
from api.utils.deps import get_current_user
from api.v1.models.user.user import User
from api.v1.services.profile_setup.profile_setup import (ProfileSetupService, ProfileSetupExistsError)
from api.v1.schemas.profile_setup.profile_setup import ProfileSetupSubmit
from api.utils.responses import success_response, fail_response
from api.utils.logger import logger

router = APIRouter(prefix="/profile-setup", tags=["Profile Setup"])


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