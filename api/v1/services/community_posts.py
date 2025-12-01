from typing import Optional, Tuple, List
from uuid import UUID
import json
from fastapi import UploadFile, Request

from sqlalchemy.orm import Session

from api.utils.logger import logger
from api.v1.models.community.posts import Post
from api.v1.models.community.post_photos import PostPhoto
from api.v1.models.photos import Photos
from api.v1.schemas.community_posts import PostCreateRequest


class CommunityPostService:
    def __init__(self, db: Session):
        self.db = db

    def create_post(
        self, *, user_id: UUID, payload: PostCreateRequest
    ) -> Tuple[Optional[Post], Optional[Tuple[int, str]]]:
        """Create post with existing photo IDs (JSON)"""
        try:
            # Validate photo IDs if provided
            if payload.photo_ids:
                is_valid, error_message = self._validate_photo_ids(payload.photo_ids)
                if not is_valid:
                    return None, (400, error_message)
            
            # Create the post using BaseModel methods
            post = Post(
                user_id=user_id, 
                title=payload.title, 
                content=payload.content
            )
            
            # Insert the post
            post.insert(self.db, commit=False)
            
            # Add photos if provided
            if payload.photo_ids:
                for photo_id in payload.photo_ids:
                    # Get the photo from database
                    photo = Photos.fetch_one(self.db, id=photo_id)
                    if not photo:
                        self.db.rollback()
                        return None, (404, f"Photo with ID {photo_id} not found")
                    
                    # Create a PostPhoto record
                    post_photo = PostPhoto(
                        post_id=post.id,
                        url=photo.image_url
                    )
                    post_photo.add(self.db)
            
            # Commit all changes
            self.db.commit()
            
            # Refresh the post to load relationships
            try:
                self.db.refresh(post)
            except Exception as exc_refresh:
                logger.warning(
                    "Failed to refresh post after creation | post_id=%s | user_id=%s | error=%s",
                    getattr(post, "id", None),
                    user_id,
                    exc_refresh,
                )

            logger.info(
                "Community post created | post_id=%s | user_id=%s | photo_count=%s", 
                post.id, 
                user_id,
                len(payload.photo_ids) if payload.photo_ids else 0
            )
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

    async def create_post_with_files(
        self,
        *,
        user_id: UUID,
        title: str,
        content: str,
        files: List[UploadFile],
        request: Request
    ) -> Tuple[Optional[Post], Optional[Tuple[int, str]]]:
        """Create post and upload files in one operation"""
        from api.v1.services.image import ImageService
        from api.utils.responses import JSONResponse
        
        try:
            # Create the post
            post = Post(
                user_id=user_id, 
                title=title, 
                content=content
            )
            post.insert(self.db, commit=False)
            
            # Upload and attach photos
            if files:
                for file in files:
                    # Use your existing ImageService to upload
                    response = await ImageService.save_and_compress_image(
                        request=request,
                        file=file,
                        db=self.db
                    )
                    
                    # Check if upload was successful
                    if isinstance(response, JSONResponse):
                        if response.status_code != 201:
                            self.db.rollback()
                            # Extract error message from response
                            response_data = response.body
                            try:
                                if hasattr(response_data, 'decode'):
                                    response_data = json.loads(response_data.decode('utf-8'))
                                else:
                                    response_data = json.loads(response_data)
                                error_msg = response_data.get('message', 'Failed to upload image')
                            except Exception as e:
                                error_msg = f"Failed to parse error response: {str(e)}"
                            return None, (response.status_code, error_msg)
                        
                        # Extract photo data from successful response
                        response_data = response.body
                        try:
                            if hasattr(response_data, 'decode'):
                                response_data = json.loads(response_data.decode('utf-8'))
                            else:
                                response_data = json.loads(response_data)
                            
                            # Check if the response has the expected structure
                            if "data" in response_data and "image_url" in response_data["data"]:
                                post_photo = PostPhoto(
                                    post_id=post.id,
                                    url=response_data["data"]["image_url"]
                                )
                                post_photo.add(self.db)
                            else:
                                logger.error(
                                    "Unexpected response structure from ImageService | response=%s",
                                    response_data
                                )
                                self.db.rollback()
                                return None, (500, "Invalid response from image service")
                        except Exception as e:
                            logger.error(
                                "Failed to parse ImageService response | error=%s",
                                str(e)
                            )
                            self.db.rollback()
                            return None, (500, "Failed to process image upload response")
                    else:
                        # Handle if response is not JSONResponse
                        self.db.rollback()
                        return None, (500, "Unexpected response from image service")
            
            # Commit all changes
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

            logger.info(
                "Community post created with files | post_id=%s | user_id=%s | file_count=%s", 
                post.id, 
                user_id,
                len(files)
            )
            return post, None

        except Exception as exc:  
            logger.error(
                "Error creating community post with files | user_id=%s | title=%s | error=%s",
                user_id,
                title,
                exc,
            )
            self.db.rollback()
            return None, (500, "Failed to create post with files")

    def _validate_photo_ids(self, photo_ids: List[UUID]) -> Tuple[bool, Optional[str]]:
        """Validate that photo IDs exist in database"""
        if not photo_ids:
            return True, None
            
        photos = Photos.fetch_all(self.db)
        existing_ids = {str(photo.id) for photo in photos}
        
        missing_ids = []
        for photo_id in photo_ids:
            if str(photo_id) not in existing_ids:
                missing_ids.append(str(photo_id))
        
        if missing_ids:
            return False, f"Photos not found: {', '.join(missing_ids)}"
        
        return True, None
    
    def get_post_with_photos(self, post_id: UUID) -> Optional[Post]:
        """
        Get a post with its photos loaded
        """
        return Post.fetch_unique(self.db, id=post_id)

    def add_photo_to_post(self, post_id: UUID, photo_id: UUID) -> Tuple[Optional[PostPhoto], Optional[Tuple[int, str]]]:
        """
        Add an existing photo to a post
        """
        try:
            # Check if post exists
            post = Post.fetch_one(self.db, id=post_id)
            if not post:
                return None, (404, "Post not found")
            
            # Check if photo exists
            photo = Photos.fetch_one(self.db, id=photo_id)
            if not photo:
                return None, (404, "Photo not found")
            
            # Check if photo is already attached to this post
            existing_photo = PostPhoto.fetch_one(self.db, post_id=post_id, url=photo.image_url)
            if existing_photo:
                return None, (400, "Photo already attached to this post")
            
            # Create PostPhoto record
            post_photo = PostPhoto(
                post_id=post_id,
                url=photo.image_url
            )
            post_photo.insert(self.db)
            
            logger.info(
                "Photo added to post | post_id=%s | photo_id=%s | post_photo_id=%s",
                post_id,
                photo_id,
                post_photo.id
            )
            return post_photo, None
            
        except Exception as exc:
            logger.error(
                "Error adding photo to post | post_id=%s | photo_id=%s | error=%s",
                post_id,
                photo_id,
                exc
            )
            return None, (500, "Failed to add photo to post")

    def remove_photo_from_post(self, post_photo_id: UUID) -> Tuple[bool, Optional[Tuple[int, str]]]:
        """
        Remove a photo from a post
        """
        try:
            post_photo = PostPhoto.fetch_one(self.db, id=post_photo_id)
            if not post_photo:
                return False, (404, "Post photo not found")
            
            post_photo.delete(self.db)
            
            logger.info(
                "Photo removed from post | post_photo_id=%s | post_id=%s",
                post_photo_id,
                post_photo.post_id
            )
            return True, None
            
        except Exception as exc:
            logger.error(
                "Error removing photo from post | post_photo_id=%s | error=%s",
                post_photo_id,
                exc
            )
            return False, (500, "Failed to remove photo from post")