"""
Chat Service - Handles chat session and message operations
"""

from sqlalchemy.orm import Session
from typing import Optional, Tuple
import uuid
from datetime import datetime, timezone

from api.v1.models.chat_session import ChatSession
from api.v1.models.chat_message import ChatMessage
from api.utils.logger import logger


def generate_title_from_message(message: str, max_length: int = 100) -> str:
    """
    Generate a conversation title from the first message.
    
    Similar to ChatGPT behavior:
    - Takes first 50-100 characters
    - Removes extra whitespace
    - Creates a meaningful title
    
    Args:
        message: The initial message from user
        max_length: Maximum length of title
        
    Returns:
        Generated title string
    """
    # Clean up the message
    title = message.strip()
    
    # Remove extra whitespace
    title = " ".join(title.split())
    
    # Truncate to max_length and add ellipsis if needed
    if len(title) > max_length:
        title = title[:max_length].rsplit(" ", 1)[0] + "..."
    
    return title


def create_new_chat_session(
    db: Session, 
    user_id: uuid.UUID, 
    initial_message: str
) -> Tuple[Optional[ChatSession], Optional[str]]:
    """
    Create a new chat session with an initial message.
    
    Args:
        db: Database session
        user_id: ID of the user creating the session
        initial_message: The first message in the conversation
        
    Returns:
        Tuple of (ChatSession object, error message)
        Returns (ChatSession, None) on success
        Returns (None, error_message) on failure
    """
    try:
        # Generate title from message
        title = generate_title_from_message(initial_message)
        
        # Create chat session
        chat_session = ChatSession(
            id=uuid.uuid4(),
            user_id=user_id,
            title=title,
            created_at=datetime.now(timezone.utc)
        )
        
        # Save session to database
        chat_session.insert(db)
        
        logger.info(f"Chat session created: {chat_session.id} for user: {user_id}")
        
        return chat_session, None
        
    except Exception as e:
        logger.error(f"Error creating chat session: {str(e)}")
        return None, f"Failed to create chat session: {str(e)}"


def add_message_to_session(
    db: Session,
    session_id: uuid.UUID,
    sender: str,
    message: str
) -> Tuple[Optional[ChatMessage], Optional[str]]:
    """
    Add a message to a chat session.
    
    Args:
        db: Database session
        session_id: ID of the chat session
        sender: Either "user" or "ai"
        message: The message content
        
    Returns:
        Tuple of (ChatMessage object, error message)
        Returns (ChatMessage, None) on success
        Returns (None, error_message) on failure
    """
    try:
        # Validate sender
        if sender not in ["user", "ai"]:
            return None, "Sender must be either 'user' or 'ai'"
        
        # Validate session exists
        session = db.query(ChatSession).filter(ChatSession.id == session_id).first()
        if not session:
            return None, f"Chat session {session_id} not found"
        
        # Create message
        chat_message = ChatMessage(
            id=uuid.uuid4(),
            session_id=session_id,
            sender=sender,
            message=message,
            created_at=datetime.now(timezone.utc)
        )
        
        # Save message to database
        chat_message.insert(db)
        
        logger.info(f"Message added to session {session_id}: {chat_message.id}")
        
        return chat_message, None
        
    except Exception as e:
        logger.error(f"Error adding message to session: {str(e)}")
        return None, f"Failed to add message: {str(e)}"
