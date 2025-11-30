from fastapi import APIRouter, Depends, status, HTTPException
from sqlalchemy.orm import Session
from uuid import UUID

from api.db.database import get_db
from api.utils.deps import get_current_user
from api.v1.models.user.user import User
from api.v1.schemas.community_posts import PostCreateRequest, PostResponse
from api.v1.services.community_posts import CommunityPostService
from api.utils.responses import success_response, fail_response
from api.utils.logger import logger


router = APIRouter(prefix="/community/posts", tags=["Community"])

@router.post("/", status_code=status.HTTP_201_CREATED, summary="Create a community post")
def create_post(
    payload: PostCreateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Create a new community post."""
    service = CommunityPostService(db)
    post, error = service.create_post(user_id=current_user.id, payload=payload)

    if error:
        status_code, message = error
        logger.warning(
            "Create post failed | user_id=%s | status=%s | message=%s",
            current_user.id,
            status_code,
            message,
        )
        return fail_response(status_code=status_code, message=message)

    response = PostResponse.model_validate(post)

    return success_response(
        status_code=status.HTTP_201_CREATED,
        message="Post created successfully",
        data=response.model_dump(),
    )



@router.delete("/{post_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Delete a community post")
def delete_post(
    post_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Delete a community post if the current user is the owner.

    Returns 204 on success, otherwise raises an HTTPException with the appropriate
    status code and error message.
    """
    service = CommunityPostService(db)
    success, error = service.delete_post(post_id=post_id, user_id=current_user.id)
    if not success:
        status_code, message = error
        raise HTTPException(status_code=status_code, detail=message)
    # FastAPI automatically returns an empty body for 204
    return
