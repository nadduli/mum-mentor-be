from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from api.db.database import get_db
from api.utils.deps import get_current_user
from api.utils.logger import logger
from api.v1.models.user.user import User

album_router = APIRouter(prefix="/albums", tags="Albums")

@album_router.post("/")
def get_album_with_memories(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    ):
    """
    Docstring for get_album_with_memories
    
    :param db: Description
    :type db: Session
    :param current_user: Description
    :type current_user: User
    """
    logger.info("Getting album with memories")
    
    
    pass
@album_router.delete()
def y():
    pass
