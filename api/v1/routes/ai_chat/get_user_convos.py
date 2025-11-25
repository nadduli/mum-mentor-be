from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from uuid import UUID

from api.db.database import get_db
from api.utils.deps import get_current_user
from api.v1.models.user.user import User
from api.v1.services.get_user_convos import ConversationService
from api.utils.responses import success_response
from api.utils.logger import logger

router = APIRouter(prefix="/chats", tags=["AI Chat"])

@router.get("/{convo_id}")
def get_user_convos(
    convo_id: UUID,
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(20, ge=1, le=100, description="Messages per page"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get a conversation (chat session) by ID with all its messages (paginated).
    
    Args:
        convo_id: UUID of the conversation
        page: Page number for pagination (default: 1)
        per_page: Number of messages per page (default: 20, max: 100)
        db: Database session
        current_user: Authenticated user
    
    Returns:
        Conversation details with paginated messages
    
    Raises:
        404: Conversation not found
        403: User does not have access to this conversation
    """    
    try:
        logger.info(f"GET /chats/{convo_id} | user_id={current_user.id} | page={page} | per_page={per_page}")
        
        conversation_service = ConversationService(db)
        
        session = conversation_service.get_conversation_by_id(convo_id, current_user.id)
        
        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Conversation not found"
            )
        
        messages, total_count = conversation_service.get_conversation_messages(
            convo_id, page, per_page
        )
        
        messages_data = [
            {
                "id": str(message.id),
                "sender": message.sender,
                "message": message.message,
                "created_at": message.created_at.isoformat()
            }
            for message in messages
        ]
        
        total_pages = (total_count + per_page - 1) // per_page if total_count > 0 else 1
        
        # Prepare response data
        response_data = {
            "conversation": {
                "id": str(session.id),
                "user_id": str(session.user_id),
                "title": session.title,
                "created_at": session.created_at.isoformat() if session.created_at else None
            },
            "messages": messages_data,
            "pagination": {
                "page": page,
                "per_page": per_page,
                "total_count": total_count,
                "total_pages": total_pages,
                "next": page + 1 if page < total_pages else None,
                "prev": page - 1 if page > 1 else None
            }
        }
        
        logger.info(f"Conversation retrieved successfully | convo_id={convo_id} | messages_count={len(messages_data)}")
        
        return success_response(
            status_code=status.HTTP_200_OK,
            message="Conversation retrieved successfully",
            data=response_data
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving conversation | convo_id={convo_id} | error={str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while retrieving the conversation"
        )