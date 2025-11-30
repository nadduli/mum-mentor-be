"""
Route for creating a child profile.
"""

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from api.db.database import get_db
from api.utils.deps import get_current_user
from api.v1.models.user.user import User
from api.v1.schemas.child_profile import CreateChildProfileRequest
from api.v1.services.child_profile_service import ChildProfileService
from api.utils.responses import success_response, fail_response
from api.utils.logger import logger

"""
Route for listing all child profiles for the current user.
"""

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from api.db.database import get_db
from api.utils.deps import get_current_user
from api.v1.models.user.user import User
from api.v1.services.child_profile_service import ChildProfileService
from api.utils.responses import success_response, fail_response
from api.utils.logger import logger

"""
Route for updating a child profile.
"""

from uuid import UUID
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from api.db.database import get_db
from api.utils.deps import get_current_user
from api.v1.models.user.user import User
from api.v1.schemas.child_profile import UpdateChildProfileRequest
from api.v1.services.child_profile_service import ChildProfileService
from api.utils.responses import success_response, fail_response
from api.utils.logger import logger

"""
Route for uploading child profile picture.
"""

from uuid import UUID
from fastapi import APIRouter, Depends, status, UploadFile, File, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from api.db.database import get_db
from api.utils.deps import get_current_user
from api.v1.models.user.user import User
from api.v1.services.child_profile_service import ChildProfileService
from api.v1.services.child_profile_image_upload import (
    save_child_profile_image,
    delete_child_profile_image,
)
from api.utils.responses import success_response, fail_response
from api.utils.logger import logger
from pathlib import Path


router = APIRouter(prefix="/child-profiles", tags=["Child Profiles"])


UPLOAD_DIR = Path("app/uploads/child_profiles")


@router.post("/{child_id}/upload-picture", status_code=status.HTTP_200_OK)
async def upload_child_profile_picture(
    child_id: UUID,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Upload a profile picture for a child.

    This endpoint allows uploading an image file for a child's profile picture.
    The image is stored locally and the URL is saved to the database.

    Supported formats: JPEG, PNG, WebP
    Maximum size: 5MB
    """
    logger.info(
        f"Uploading profile picture for child {child_id} by user {current_user.id}"
    )

    try:
        # Get child profile and verify ownership
        child = ChildProfileService.get_child_profile(
            db=db, child_id=child_id, user_id=current_user.id
        )

        if not child:
            return fail_response(
                status_code=status.HTTP_404_NOT_FOUND,
                message="Child profile not found",
                context={"child_id": str(child_id)},
            )

        # Delete old image if exists
        if child.get("profile_picture_url"):
            delete_child_profile_image(child["profile_picture_url"])

        # Upload new image
        image_url = await save_child_profile_image(file)

        # Update database
        from api.v1.schemas.child_profile import UpdateChildProfileRequest

        update_request = UpdateChildProfileRequest(profile_picture_url=image_url)

        updated_child = ChildProfileService.update_child_profile(
            db=db, child_id=child_id, user_id=current_user.id, request=update_request
        )

        return success_response(
            status_code=status.HTTP_200_OK,
            message="Profile picture uploaded successfully",
            data=updated_child,
        )

    except Exception as e:
        logger.error(f"Error uploading profile picture for child {child_id}: {e}")
        return fail_response(
            status_code=getattr(
                e, "status_code", status.HTTP_500_INTERNAL_SERVER_ERROR
            ),
            message=getattr(e, "detail", "Failed to upload profile picture"),
            context={"error": str(e)},
        )


@router.get("/avatar/{filename}", status_code=status.HTTP_200_OK)
async def get_child_avatar(filename: str):
    """
    Serve child profile avatar image.

    **Public endpoint - no authentication required**

    This allows avatars to be displayed without authentication,
    making them usable in <img> tags and shareable.
    """
    file_path = UPLOAD_DIR / filename

    if not file_path.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Avatar image not found"
        )

    # Determine media type based on file extension
    ext = filename.split(".")[-1].lower()
    media_types = {
        "jpg": "image/jpeg",
        "jpeg": "image/jpeg",
        "png": "image/png",
        "webp": "image/webp",
    }
    media_type = media_types.get(ext, "image/jpeg")

    return FileResponse(path=str(file_path), media_type=media_type, filename=filename)


router = APIRouter(prefix="/child-profiles", tags=["Child Profiles"])


@router.patch("/{child_id}", status_code=status.HTTP_200_OK)
def update_child_profile(
    child_id: UUID,
    request: UpdateChildProfileRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Update a child profile.

    Only fields provided in the request will be updated (partial update).
    """
    logger.info(f"Updating child profile {child_id} for user {current_user.id}")

    try:
        child = ChildProfileService.update_child_profile(
            db=db, child_id=child_id, user_id=current_user.id, request=request
        )

        return success_response(
            status_code=status.HTTP_200_OK,
            message="Child profile updated successfully",
            data=child,
        )

    except Exception as e:
        logger.error(f"Error updating child profile {child_id}: {e}")
        return fail_response(
            status_code=getattr(
                e, "status_code", status.HTTP_500_INTERNAL_SERVER_ERROR
            ),
            message=getattr(e, "detail", "Failed to update child profile"),
            context={"error": str(e)},
        )


router = APIRouter(prefix="/child-profiles", tags=["Child Profiles"])


@router.get("/", status_code=status.HTTP_200_OK)
def list_child_profiles(
    db: Session = Depends(get_db), current_user: User = Depends(get_current_user)
):
    """
    Get all child profiles for the current user.

    Returns an empty list if the user has no children.
    """
    logger.info(f"Listing child profiles for user {current_user.id}")

    try:
        children = ChildProfileService.get_all_child_profiles(
            db=db, user_id=current_user.id
        )

        return success_response(
            status_code=status.HTTP_200_OK,
            message="Child profiles retrieved successfully",
            data={"children": children, "total": len(children)},
        )

    except Exception as e:
        logger.error(f"Error listing child profiles for user {current_user.id}: {e}")
        return fail_response(
            status_code=getattr(
                e, "status_code", status.HTTP_500_INTERNAL_SERVER_ERROR
            ),
            message=getattr(e, "detail", "Failed to retrieve child profiles"),
            context={"error": str(e)},
        )


"""
Route for getting a single child profile.
"""

from uuid import UUID
from fastapi import APIRouter, Depends, status, HTTPException
from sqlalchemy.orm import Session

from api.db.database import get_db
from api.utils.deps import get_current_user
from api.v1.models.user.user import User
from api.v1.services.child_profile_service import ChildProfileService
from api.utils.responses import success_response, fail_response
from api.utils.logger import logger


router = APIRouter(prefix="/child-profiles", tags=["Child Profiles"])


@router.get("/{child_id}", status_code=status.HTTP_200_OK)
def get_child_profile(
    child_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Get a single child profile by ID.

    Only returns the child profile if it belongs to the current user.
    """
    logger.info(f"Getting child profile {child_id} for user {current_user.id}")

    try:
        child = ChildProfileService.get_child_profile(
            db=db, child_id=child_id, user_id=current_user.id
        )

        if not child:
            return fail_response(
                status_code=status.HTTP_404_NOT_FOUND,
                message="Child profile not found",
                context={"child_id": str(child_id)},
            )

        return success_response(
            status_code=status.HTTP_200_OK,
            message="Child profile retrieved successfully",
            data=child,
        )

    except Exception as e:
        logger.error(f"Error getting child profile {child_id}: {e}")
        return fail_response(
            status_code=getattr(
                e, "status_code", status.HTTP_500_INTERNAL_SERVER_ERROR
            ),
            message=getattr(e, "detail", "Failed to retrieve child profile"),
            context={"error": str(e)},
        )


"""
Route for deleting a child profile.
"""

from uuid import UUID
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from api.db.database import get_db
from api.utils.deps import get_current_user
from api.v1.models.user.user import User
from api.v1.services.child_profile_service import ChildProfileService
from api.v1.services.child_profile_image_upload import delete_child_profile_image
from api.utils.responses import success_response, fail_response
from api.utils.logger import logger


router = APIRouter(prefix="/child-profiles", tags=["Child Profiles"])


@router.delete("/{child_id}", status_code=status.HTTP_200_OK)
def delete_child_profile(
    child_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Delete a child profile.

    This is a hard delete operation that also removes the profile picture from storage.
    """
    logger.info(f"Deleting child profile {child_id} for user {current_user.id}")

    try:
        # Get child profile first to get image URL
        child = ChildProfileService.get_child_profile(
            db=db, child_id=child_id, user_id=current_user.id
        )

        if not child:
            return fail_response(
                status_code=status.HTTP_404_NOT_FOUND,
                message="Child profile not found",
                context={"child_id": str(child_id)},
            )

        # Delete profile picture if exists
        if child.get("profile_picture_url"):
            delete_child_profile_image(child["profile_picture_url"])
            logger.info(f"Deleted profile picture for child {child_id}")

        # Delete child profile from database
        success = ChildProfileService.delete_child_profile(
            db=db, child_id=child_id, user_id=current_user.id
        )

        if success:
            return success_response(
                status_code=status.HTTP_200_OK,
                message="Child profile deleted successfully",
                data={"deleted": True, "child_id": str(child_id)},
            )
        else:
            return fail_response(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                message="Failed to delete child profile",
                context={"child_id": str(child_id)},
            )

    except Exception as e:
        logger.error(f"Error deleting child profile {child_id}: {e}")
        return fail_response(
            status_code=getattr(
                e, "status_code", status.HTTP_500_INTERNAL_SERVER_ERROR
            ),
            message=getattr(e, "detail", "Failed to delete child profile"),
            context={"error": str(e)},
        )


router = APIRouter(prefix="/child-profiles", tags=["Child Profiles"])


@router.post("/", status_code=status.HTTP_201_CREATED)
def create_child_profile(
    request: CreateChildProfileRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Create a new child profile.

    The child profile will be linked to the user's profile setup.
    """
    logger.info(f"Creating child profile for user {current_user.id}")

    try:
        child = ChildProfileService.create_child_profile(
            db=db, user_id=current_user.id, request=request
        )

        return success_response(
            status_code=status.HTTP_201_CREATED,
            message="Child profile created successfully",
            data=child,
        )

    except Exception as e:
        logger.error(f"Error creating child profile: {e}")
        return fail_response(
            status_code=getattr(
                e, "status_code", status.HTTP_500_INTERNAL_SERVER_ERROR
            ),
            message=getattr(e, "detail", "Failed to create child profile"),
            context={"error": str(e)},
        )
