from sqlalchemy.orm import Session
from uuid import UUID
from api.v1.models.albums import Album
from api.utils.logger import logger

def create_album(db: Session, user_id: UUID, name: str):
    album = Album(
        name=name,
        user_id=user_id
    )
    db.add(album)
    db.commit()
    db.refresh(album)
    logger.info(f"Album created: {album.id} by user {user_id}")
    return album

def delete_album(db: Session, album_id: UUID, user_id: UUID):
    album = db.query(Album).filter(
        Album.id == album_id,
        Album.user_id == user_id
    ).first()

    if not album:
        return None, "Album not found"

    db.delete(album)
    db.commit()
    logger.info(f"Album deleted: {album_id} by user {user_id}")
    return True, None
