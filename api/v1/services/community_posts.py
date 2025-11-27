from typing import Optional, Tuple
from uuid import UUID

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
            # Some SQLAlchemy setups require refresh to populate defaults
            try:
                self.db.refresh(post)
            except Exception:
                # ignore refresh errors in test environments
                pass

            logger.info("Community post created | post_id=%s | user_id=%s", post.id, user_id)
            return post, None

        except Exception as exc:  # pragma: no cover - defensive logging
            logger.error(
                "Error creating community post | user_id=%s | title=%s | error=%s",
                user_id,
                payload.title,
                exc,
            )
            self.db.rollback()
            return None, (500, "Failed to create post")
