"""
This module contains the API endpoints for managing community posts.
"""
from uuid import UUID

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from api.db.database import get_db
from api.utils.deps import get_current_user
from api.v1.models.user.user import User
from api.v1.services.community import CommunityService
from api.v1.schemas.community import (
    PostResponse,
    PostResponseWrapper,
    PostPhotoDTO,
    LikeToggleResponse,
    LikeResponseWrapper,
)
from api.v1.schemas.community_posts import PostCreateRequest
from api.v1.services.community_posts import CommunityPostService
from api.utils.responses import success_response, fail_response
from api.utils.logger import logger

router = APIRouter(prefix="/community/posts", tags=["Community"])


@router.get(
    "/{post_id}",
    status_code=status.HTTP_200_OK,
    response_model=PostResponseWrapper,
)
def view_post(
    post_id: UUID,
    session: Session = Depends(get_db),
):
    """
    Get a single post by ID.
    Increments the view count.
    **Requires Authentication.**
    """
    post = CommunityService.get_post_by_id(session, post_id)

    response_data = PostResponse(
        id=post.id,
        title=post.title,
        content=post.content,
        created_at=post.created_at,
        views=post.views,
        photos=[PostPhotoDTO.model_validate(p) for p in post.photos],
        likes_count=len(post.likes),
        comments_count=len(post.comments),
    )

    return PostResponseWrapper(
        status="success", message="Post retrieved successfully", data=response_data
    )


@router.post(
    "/{post_id}/like",
    status_code=status.HTTP_200_OK,
    response_model=LikeResponseWrapper,
)
def toggle_post_like(
    post_id: UUID,
    session: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Like or unlike a post (toggle).

    Returns the current like status and total likes count.
    **Requires Authentication.**
    """
    # current_user.id is already a string UUID
    user_uuid = current_user.id
    is_liked, likes_count = CommunityService.toggle_post_like(
        session, post_id, user_uuid
    )

    message = "Post liked successfully" if is_liked else "Post unliked successfully"

    return LikeResponseWrapper(
        status="success",
        message=message,
        data=LikeToggleResponse(is_liked=is_liked, likes_count=likes_count),
    )


@router.post(
    "/", status_code=status.HTTP_201_CREATED, summary="Create a community post"
)
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
