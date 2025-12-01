from typing import Optional, Tuple, List
from uuid import UUID
from datetime import datetime

from sqlalchemy.orm import Session

from api.utils.logger import logger
from api.v1.models.community.posts import Post
from api.v1.schemas.community_posts import PostCreateRequest


class CommunityPostService:
    def __init__(self, db: Session):
        self.db = db

    def create_post(
        self, *, user_id: UUID, payload: PostCreateRequest
    ) -> Tuple[Optional[Post], Optional[Tuple[int, str]]]:
        try:
            post = Post(user_id=user_id, title=payload.title, content=payload.content)
            self.db.add(post)
            self.db.commit()
            try:
                self.db.refresh(post)
            except Exception as exc_refresh:
                logger.warning(
                    "Failed to refresh post after creation | post_id=%s | user_id=%s | error=%s",
                    getattr(post, "id", None),
                    user_id,
                    exc_refresh,
                )

            logger.info("Community post created | post_id=%s | user_id=%s", post.id, user_id)
            return post, None

        except Exception as exc:  
            logger.error(
                "Error creating community post | user_id=%s | title=%s | error=%s",
                user_id,
                payload.title,
                exc,
            )
            self.db.rollback()
            return None, (500, "Failed to create post")

    def list_posts(
        self,
        *,
        page: int = 1,
        per_page: int = 20,
        cursor: Optional[str] = None,
    ) -> Tuple[Optional[dict], Optional[Tuple[int, str]]]:
        """Return paginated posts ordered by newest first.

        Supports two modes:
        - Keyset pagination when `cursor` (ISO datetime string) is provided: returns posts with created_at < cursor.
        - Offset pagination when `cursor` is None: uses page/per_page with OFFSET.

        Always returns a dict with `items` (list of Post), `total` (int) and `next_cursor` (str|None).
        """
        try:
            if page < 1:
                page = 1
            if per_page < 1:
                per_page = 20

            # Base query ordered newest-first
            query = self.db.query(Post).order_by(Post.created_at.desc(), Post.id.desc())

            # Keyset pagination: use cursor (ISO datetime) to fetch items created before the cursor
            next_cursor: Optional[str] = None
            if cursor:
                try:
                    cursor_dt = datetime.fromisoformat(cursor)
                except Exception:
                    return None, (400, "Invalid cursor format; expected ISO datetime")

                items: List[Post] = (
                    query.filter(Post.created_at < cursor_dt).limit(per_page).all()
                )

            else:
                # Offset pagination fallback
                items = query.offset((page - 1) * per_page).limit(per_page).all()

            # Compute next cursor for keyset clients (use last item's created_at)
            if items:
                last = items[-1]
                # Use ISO format (UTC-aware)
                try:
                    next_cursor = last.created_at.isoformat()
                except Exception:
                    next_cursor = None

            # Total count (kept for compatibility with existing responses)
            total = self.db.query(Post).count()

            result = {"items": items, "total": total, "next_cursor": next_cursor}
            return result, None

        except Exception as exc:
            logger.error("Error listing posts | page=%s | per_page=%s | error=%s", page, per_page, exc)
            return None, (500, "Failed to fetch posts")
