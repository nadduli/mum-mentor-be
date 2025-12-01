"""
This module contains the API endpoints for managing community posts.
"""
from typing import Optional
from uuid import UUID
from typing import List

from fastapi import APIRouter, Depends, status, Form, File, UploadFile, Request
from sqlalchemy.orm import Session

from api.db.database import get_db
from api.utils.deps import get_current_user
from api.v1.models.user.user import User
from api.v1.services.community import CommunityService
from api.v1.schemas.community_posts import CommentCreateRequest 
from api.v1.schemas.community import (
    PostResponse,
    PostResponseWrapper,
    PostPhotoDTO,
    LikeToggleResponse,
    LikeResponseWrapper,
)
from api.v1.schemas.community_posts import PostCreateRequest, PostPhotoResponse
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
    "/", 
    status_code=status.HTTP_201_CREATED, 
    summary="Create a community post with existing photos"
)
def create_post_json(
    payload: PostCreateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Create a new community post using existing photo IDs.
    
    JSON Request:
    {
        "title": "My Post",
        "content": "Content here",
        "photo_ids": ["uuid1", "uuid2"]  # Optional - existing photo IDs
    }
    
    **Requires Authentication.**
    """
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

    # Convert photos to response format
    photos_response = []
    if post.photos:
        photos_response = [
            PostPhotoResponse(
                id=photo.id,
                post_id=photo.post_id,
                url=photo.url
            ) for photo in post.photos
        ]
    
    response_data = {
        "id": post.id,
        "user_id": post.user_id,
        "title": post.title,
        "content": post.content,
        "created_at": post.created_at,
        "views": post.views,
        "photos": photos_response
    }

    return success_response(
        status_code=status.HTTP_201_CREATED,
        message="Post created successfully",
        data=response_data,
    )

@router.get("/", status_code=status.HTTP_200_OK, summary="List community posts (public feed)")
def list_posts(
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(20, ge=1, le=100, description="Number of posts per page"),
    cursor: Optional[str] = Query(None, description="Keyset cursor in format '<ISO datetime>|<uuid>'. If set, uses keyset pagination and ignores page."),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Return paginated community posts ordered by newest first (public feed)."""
    service = CommunityPostService(db)
    result, error = service.list_posts(page=page, per_page=per_page, cursor=cursor)

@router.post(
    "/upload",
    status_code=status.HTTP_201_CREATED,
    summary="Create a community post with photo uploads"
)
async def create_post_with_upload(
    request: Request,
    title: str = Form(..., description="Post title"),
    content: str = Form(..., description="Post content"),
    files: List[UploadFile] = File(..., description="Image files to upload"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Create a new community post and upload photos in one request.
    
    Form Data:
    - title: string
    - content: string
    - files: list of image files
    
    **Requires Authentication.**
    """
    service = CommunityPostService(db)
    
    post, error = await service.create_post_with_files(
        user_id=current_user.id,
        title=title,
        content=content,
        files=files,
        request=request
        # Note: db is already passed to service constructor
    )

    if error:
        status_code, message = error
        logger.warning(
            "List posts failed | page=%s | per_page=%s | status=%s | message=%s",
            page,
            per_page,
            "Create post with upload failed | user_id=%s | status=%s | message=%s",
            current_user.id,
            status_code,
            message,
        )
        return fail_response(status_code=status_code, message=message)

    items = result.get("items", [])
    total = result.get("total", 0)
    next_cursor = result.get("next_cursor")

    posts_data = [PostResponse.model_validate(item).model_dump() for item in items]

    total_pages = 0
    try:
        total_pages = (total + per_page - 1) // per_page if per_page else 0
    except Exception:
        total_pages = 0

    data = {
        "posts": posts_data,
        "meta": {
            "page": page if not cursor else None,
            "per_page": per_page,
            "total": total,
            "total_pages": total_pages if not cursor else None,
            "next_cursor": next_cursor,
        },
    }

    return success_response(status_code=status.HTTP_200_OK, message="Posts fetched successfully", data=data)
    # Convert photos to response format
    photos_response = []
    if post.photos:
        photos_response = [
            PostPhotoResponse(
                id=photo.id,
                post_id=photo.post_id,
                url=photo.url
            ) for photo in post.photos
        ]
    
    response_data = {
        "id": post.id,
        "user_id": post.user_id,
        "title": post.title,
        "content": post.content,
        "created_at": post.created_at,
        "views": post.views,
        "photos": photos_response
    }

    return success_response(
        status_code=status.HTTP_201_CREATED,
        message="Post created successfully",
        data=response_data,
    )


@router.post("/{post_id}/comment", status_code=status.HTTP_201_CREATED)
def comment_on_post(
    post_id: UUID,
    payload: CommentCreateRequest,
    session: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Adds a comment to a community post.
    """
    comment = CommunityService.add_comment_to_post(
        session, post_id, current_user.id, payload.comment
    )
    return success_response(
        status_code=status.HTTP_201_CREATED,
        message="Comment added successfully",
        data={"id": str(comment.id), "comment": comment.comment}
    )
