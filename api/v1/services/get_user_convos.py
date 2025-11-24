from uuid import UUID
from typing import Optional, Tuple, List
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from api.v1.models.chat_session import ChatSession
from api.v1.models.chat_message import ChatMessage
from api.v1.models.user.user import User
from api.utils.logger import logger


class ConversationService:
    """Service for conversation and chat message operations"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_conversation_by_id(
        self, 
        convo_id: UUID, 
        user_id: UUID
    ) -> Optional[ChatSession]:
        """
        Retrieve a conversation by ID for a specific user.
        
        Args:
            convo_id: UUID of the conversation
            user_id: UUID of the user who owns the conversation
        
        Returns:
            ChatSession object if found and user has access, None otherwise
        
        Raises:
            HTTPException: If conversation not found or user doesn't have access
        """
        try:
            logger.info(f"Fetching conversation | convo_id={convo_id} | user_id={user_id}")
            
            # Get conversation by ID
            session = self.db.query(ChatSession).filter(
                ChatSession.id == convo_id
            ).first()
            
            # Return None if conversation doesn't exist
            if not session:
                logger.warning(f"Conversation not found | convo_id={convo_id}")
                return None
            
            # Check if user has access to this conversation
            if session.user_id != user_id:
                logger.warning(f"Unauthorized access attempt | convo_id={convo_id} | user_id={user_id}")
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="You do not have access to this conversation"
                )
            
            return session
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error fetching conversation | convo_id={convo_id} | error={str(e)}")
            raise
    
    def get_conversation_messages(
        self, 
        convo_id: UUID, 
        page: int = 1, 
        per_page: int = 20
    ) -> Tuple[List[ChatMessage], int]:
        """
        Retrieve paginated messages for a conversation.
        
        Args:
            convo_id: UUID of the conversation
            page: Page number for pagination
            per_page: Number of messages per page
        
        Returns:
            Tuple of (list of ChatMessage objects, total count)
        """
        try:
            logger.info(f"Fetching messages | convo_id={convo_id} | page={page} | per_page={per_page}")
            
            # Get total count of messages in this session
            total_count = self.db.query(ChatMessage).filter(
                ChatMessage.session_id == convo_id
            ).count()
            
            # Get paginated messages for this session (ordered by creation time)
            offset = (page - 1) * per_page
            messages = self.db.query(ChatMessage).filter(
                ChatMessage.session_id == convo_id
            ).order_by(
                ChatMessage.created_at.asc()
            ).limit(per_page).offset(offset).all()
            
            logger.info(f"Messages retrieved | convo_id={convo_id} | count={len(messages)} | total={total_count}")
            
            return messages, total_count
            
        except Exception as e:
            logger.error(f"Error fetching messages | convo_id={convo_id} | error={str(e)}")
            raise
        