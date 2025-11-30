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

    def delete_post(self, *, post_id: UUID, user_id: UUID) -> Tuple[bool, Optional[Tuple[int, str]]]:
        """Delete a community post if it belongs to the given user.

        Returns:
            (True, None) on success.
            (False, (status_code, message)) on failure.
        """
        try:
            # Fetch the post
            post = self.db.query(Post).filter(Post.id == post_id).with_for_update().first()
            if not post:
                return False, (404, "Post not found")

            # Authorization check
            if post.user_id != user_id:
                return False, (403, "Not authorized to delete this post")

            # Perform deletion
            self.db.delete(post)
            self.db.commit()
            logger.info("Community post deleted | post_id=%s | user_id=%s", post_id, user_id)
            return True, None
        except Exception as exc:
            self.db.rollback()
            logger.error(
                "Error deleting community post | post_id=%s | user_id=%s | error=%s",
                post_id,
                user_id,
                exc,
            )
            return False, (500, "Failed to delete post")
