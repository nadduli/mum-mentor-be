"""
Create New Chat Session Endpoint
"""

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from datetime import datetime, timezone

from api.db.database import get_db
from api.utils.deps import get_current_user
from api.v1.models.user.user import User
from api.v1.models.chat_session import ChatSession
from api.v1.schemas.ai_chat import ChatSessionResponse
from api.utils.responses import success_response
from api.utils.logger import logger


router = APIRouter(prefix="/chats", tags=["AI Chat"])


@router.post("/", status_code=status.HTTP_201_CREATED)
def create_chat_session(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Create a new chat session for the current user
    
    The title will be automatically generated when the user sends their first message.
    
    Args:
        db: Database session
        current_user: Authenticated user
    
    Returns:
        Created chat session details (title will be None initially)
    """
    try:
        logger.info(f"Creating new chat session | user_id={current_user.id}")
        
        # Create new session without title (will be generated on first message)
        session = ChatSession(
            user_id=current_user.id,
            title=None,
            created_at=datetime.now(timezone.utc)
        )
        
        db.add(session)
        db.commit()
        db.refresh(session)
        
        logger.info(f"Chat session created | session_id={session.id} | user_id={current_user.id}")
        
        # Prepare response
        session_data = {
            "id": str(session.id),
            "user_id": str(session.user_id),
            "title": session.title,
            "created_at": session.created_at.isoformat()
        }
        
        return success_response(
            status_code=status.HTTP_201_CREATED,
            message="Chat session created successfully",
            data=session_data
        )
    
    except Exception as e:
        logger.error(f"Error creating chat session | user_id={current_user.id} | error={str(e)}")
        raise
