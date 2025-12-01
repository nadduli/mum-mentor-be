from typing import Optional, Tuple, List
from uuid import UUID
from datetime import datetime
from sqlalchemy import and_, or_

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

        Always returns a dict with `items` (list of Post), `total` (int|None) and `next_cursor` (str|None).
        """
        try:
            if page < 1:
                page = 1
            if per_page < 1:
                per_page = 20

            # Base query ordered newest-first
            query = self.db.query(Post).order_by(Post.created_at.desc(), Post.id.desc())

            # Keyset pagination: expect cursor as "<iso_datetime>|<uuid>" to handle ties
            next_cursor: Optional[str] = None
            items: List[Post] = []

            if cursor:
                # parse cursor into (created_at, id)
                try:
                    created_at_str, id_str = cursor.split("|", 1)
                    # support trailing Z (UTC) by replacing Z with +00:00
                    if created_at_str.endswith("Z"):
                        created_at_str = created_at_str[:-1] + "+00:00"
                    cursor_dt = datetime.fromisoformat(created_at_str)
                    cursor_id = UUID(id_str)
                except Exception as exc:
                    logger.exception("Invalid cursor provided: %s", cursor)
                    return None, (400, "Invalid cursor format; expected '<ISO datetime>|<uuid>'")

                # Filter to records strictly older than the cursor (created_at < cursor_dt)
                # or same timestamp but id < cursor_id (because we order by id desc)
                items = (
                    query.filter(
                        or_(
                            Post.created_at < cursor_dt,
                            and_(Post.created_at == cursor_dt, Post.id < cursor_id),
                        )
                    )
                    .limit(per_page)
                    .all()
                )

                # For keyset pagination we avoid an expensive full COUNT; set total to None
                total = None

            else:
                # Offset pagination fallback (keeps total count for compatibility)
                items = query.offset((page - 1) * per_page).limit(per_page).all()
                try:
                    total = self.db.query(Post).count()
                except Exception:
                    logger.exception("Failed to compute total count for posts")
                    total = None

            # Compute next cursor for keyset clients (use last item's created_at and id)
            if items:
                last = items[-1]
                try:
                    next_cursor = f"{last.created_at.isoformat()}|{last.id}"
                except Exception:
                    logger.exception("Failed to compute next_cursor for post id=%s", getattr(last, "id", None))
                    next_cursor = None

            result = {"items": items, "total": total, "next_cursor": next_cursor}
            return result, None

        except Exception as exc:
            logger.error("Error listing posts | page=%s | per_page=%s | error=%s", page, per_page, exc)
            return None, (500, "Failed to fetch posts")
