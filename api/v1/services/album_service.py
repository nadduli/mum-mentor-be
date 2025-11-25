from sqlalchemy.orm import Session, joinedload
from sqlalchemy import select
from api.v1.models.albums import Album
from api.v1.models.memories import Memory
from api.v1.models.photos import Photos
import uuid


class AlbumService:
    """Service for album operations"""

    def __init__(self, db: Session):
        self.db = db

    def get_album_with_memories_by_id(self, album_id: uuid.UUID, user_id: uuid.UUID) -> Album | None:
        """
        Get an album with all its memories and photos by album ID for a specific user.

        Args:
            album_id: The UUID of the album
            user_id: The UUID of the user who owns the album

        Returns:
            Album object with loaded memories and photos, or None if not found
        """
        # Query album with joined memories and photos
        stmt = (
            select(Album)
            .options(
                joinedload(Album.memories).joinedload(Memory.photo_data)
            )
            .where(Album.id == album_id, Album.user_id == user_id)
        )

        result = self.db.execute(stmt)
        album = result.unique().scalar_one_or_none()

        return album