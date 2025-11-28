from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from api.db.database import get_db
from api.utils.deps import get_current_user
from api.utils.responses import success_response, fail_response
from api.v1.models.user.user import User
from api.v1.schemas.resource import CreateResourceBookmark
from api.v1.services.create_resource_bookmark import create_resource_bookmark

save_resources_router = APIRouter(prefix="/resource/bookmarks", tags=["Resources"])

@save_resources_router.post("/")
async def save_resource_for_later(
    payload: CreateResourceBookmark,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Create a bookmark for a resource for the current user.

    This endpoint allows an authenticated user to save a resource for later access (bookmark).
    It expects a payload with the resource ID, and will associate the resource with the user.
    Returns a success response with the bookmark details, or an error if the operation fails.
    """
    try:
        new_bookmark = create_resource_bookmark(
            db, current_user.id, payload.resource_id
        )
        return success_response(
            status_code=status.HTTP_201_CREATED,
            message="Successfully created resource for later",
            data=new_bookmark,
        )
    except Exception as e:
        return fail_response(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            message="Something went wrong while trying to save your resource bookmark",
            context=str(e),
        )