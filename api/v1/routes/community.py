from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
import uuid

from api.db.database import get_db
from api.v1.dependencies.auth import get_current_user
from api.v1.services.community import CommunityService
from api.v1.schemas.community import PostResponse, PostResponseWrapper, PostPhotoDTO

router = APIRouter(prefix="/community", tags=["Community"])

@router.get("/posts/{post_id}", status_code=status.HTTP_200_OK, response_model=PostResponseWrapper)
def view_post(
    post_id: uuid.UUID,
    session: Session = Depends(get_db),
    current_user = Depends(get_current_user)
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
        comments_count=len(post.comments)
    )

    return PostResponseWrapper(
        status="success",
        message="Post retrieved successfully",
        data=response_data
    )