from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from api.db.database import get_db
from api.utils.deps import get_current_user
from api.v1.models.user.user import User
from api.v1.schemas.community_posts import PostCreateRequest, PostResponse
from api.v1.services.community_posts import CommunityPostService
from api.utils.responses import success_response, fail_response
from api.utils.logger import logger


router = APIRouter(prefix="/community/posts", tags=["Community Posts"])

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


@router.get("/", status_code=status.HTTP_200_OK, summary="List community posts (feed)")
def list_posts(
    page: int = 1,
    per_page: int = 20,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Return paginated community posts ordered by newest first (public feed)."""
    service = CommunityPostService(db)
    result, error = service.list_posts(page=page, per_page=per_page)

    if error:
        status_code, message = error
        logger.warning(
            "List posts failed | page=%s | per_page=%s | status=%s | message=%s",
            page,
            per_page,
            status_code,
            message,
        )
        return fail_response(status_code=status_code, message=message)

    items = result.get("items", [])
    total = result.get("total", 0)

    posts_data = [PostResponse.model_validate(item).model_dump() for item in items]

    total_pages = 0
    try:
        total_pages = (total + per_page - 1) // per_page if per_page else 0
    except Exception:
        total_pages = 0

    data = {
        "posts": posts_data,
        "meta": {
            "page": page,
            "per_page": per_page,
            "total": total,
            "total_pages": total_pages,
        },
    }

    return success_response(status_code=status.HTTP_200_OK, message="Posts fetched successfully", data=data)
