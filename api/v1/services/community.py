from sqlalchemy.orm import Session, joinedload
from fastapi import HTTPException, status
import uuid

from api.v1.models.community.posts import Post
from api.utils.logger import logger

class CommunityService:
    
    @staticmethod
    def get_post_by_id(session: Session, post_id: uuid.UUID) -> Post:
        """
        Fetches a post by ID, eager loads photos, and increments view count.
        """
        logger.info(f"Fetching post details for {post_id}")

        post = session.query(Post).options(
            joinedload(Post.photos),
            joinedload(Post.likes),  
            joinedload(Post.comments)
        ).filter(Post.id == post_id).first()

        if not post:
            logger.warning(f"Post {post_id} not found")
            raise HTTPException(status_code=404, detail="Post not found")

        post.views += 1
        try:
            session.commit()
            session.refresh(post)
        except Exception as e:
            logger.error(f"Failed to update view count for post {post_id}: {e}")
            session.rollback()

        return post