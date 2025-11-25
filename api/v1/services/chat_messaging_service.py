"""
AI Chat Messaging Service
Handles message creation, context management, and AI interaction
"""

from uuid import UUID
from typing import AsyncGenerator, Optional, Tuple
from sqlalchemy.orm import Session
from fastapi import HTTPException, status, BackgroundTasks

from api.v1.models.chat_session import ChatSession
from api.v1.models.chat_message import ChatMessage
from api.v1.services.openrouter_service import OpenRouterService
from api.utils.logger import logger


class ChatMessagingService:
    """Service for managing chat messages and AI interactions"""
    
    # Context management thresholds
    MESSAGE_SUMMARY_THRESHOLD = 50
    RECENT_MESSAGES_COUNT = 20
    
    def __init__(self, db: Session):
        self.db = db
        self.openrouter = OpenRouterService()
    
    def get_session(self, session_id: UUID, user_id: UUID) -> ChatSession:
        """
        Get a chat session and verify user ownership
        
        Args:
            session_id: UUID of the session
            user_id: UUID of the user
        
        Returns:
            ChatSession object
        
        Raises:
            HTTPException: 404 if not found, 403 if unauthorized
        """
        session = self.db.query(ChatSession).filter(
            ChatSession.id == session_id
        ).first()
        
        if not session:
            logger.warning(f"Session not found | session_id={session_id}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Chat session not found"
            )
        
        if session.user_id != user_id:
            logger.warning(f"Unauthorized access | session_id={session_id} | user_id={user_id}")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have access to this chat session"
            )
        
        return session
    
    def save_user_message(self, session_id: UUID, content: str) -> ChatMessage:
        """
        Save user message to database
        
        Args:
            session_id: UUID of the chat session
            content: Message content
        
        Returns:
            Created ChatMessage object
        """
        message = ChatMessage(
            session_id=session_id,
            sender="user",
            message=content
        )
        
        self.db.add(message)
        self.db.commit()
        self.db.refresh(message)
        
        logger.info(f"User message saved | session_id={session_id} | message_id={message.id}")
        return message
    
    def save_ai_message(self, session_id: UUID, content: str) -> ChatMessage:
        """
        Save AI response to database
        
        Args:
            session_id: UUID of the chat session
            content: AI response content
        
        Returns:
            Created ChatMessage object
        """
        message = ChatMessage(
            session_id=session_id,
            sender="ai",
            message=content
        )
        
        self.db.add(message)
        self.db.commit()
        self.db.refresh(message)
        
        logger.info(f"AI message saved | session_id={session_id} | message_id={message.id} | length={len(content)}")
        return message
    
    def get_message_count(self, session_id: UUID) -> int:
        """Get total message count for a session"""
        count = self.db.query(ChatMessage).filter(
            ChatMessage.session_id == session_id
        ).count()
        
        logger.info(f"Message count | session_id={session_id} | count={count}")
        return count
    
    def get_recent_messages(self, session_id: UUID, limit: int = RECENT_MESSAGES_COUNT) -> list[ChatMessage]:
        """
        Get recent messages from a session
        
        Args:
            session_id: UUID of the session
            limit: Number of recent messages to retrieve
        
        Returns:
            List of ChatMessage objects, ordered chronologically
        """
        messages = self.db.query(ChatMessage).filter(
            ChatMessage.session_id == session_id
        ).order_by(
            ChatMessage.created_at.desc()
        ).limit(limit).all()
        
        # Reverse to get chronological order
        messages.reverse()
        
        return messages
    
    async def generate_summary_if_needed(self, session: ChatSession) -> None:
        """
        Generate conversation summary if message count exceeds threshold
        and no summary exists yet
        
        Args:
            session: ChatSession object
        """
        if session.summary is not None:
            logger.info(f"Summary already exists | session_id={session.id}")
            return
        
        message_count = self.get_message_count(session.id)
        
        if message_count <= self.MESSAGE_SUMMARY_THRESHOLD:
            logger.info(f"Message count below threshold | session_id={session.id} | count={message_count}")
            return
        
        logger.info(f"Generating summary | session_id={session.id} | message_count={message_count}")
        
        # Get all messages except the most recent ones
        all_messages = self.db.query(ChatMessage).filter(
            ChatMessage.session_id == session.id
        ).order_by(
            ChatMessage.created_at.asc()
        ).limit(message_count - self.RECENT_MESSAGES_COUNT).all()
        
        # Format conversation history for summarization
        conversation_text = "\n".join([
            f"{msg.sender.upper()}: {msg.message}"
            for msg in all_messages
        ])
        
        # Generate summary
        try:
            summary = await self.openrouter.generate_summary(conversation_text)
            
            # Update session with summary
            session.summary = summary
            self.db.commit()
            
            logger.info(f"Summary generated and saved | session_id={session.id} | summary_length={len(summary)}")
        except Exception as e:
            logger.error(f"Failed to generate summary | session_id={session.id} | error={str(e)}")
            # Don't raise - summarization failure shouldn't block messaging
    
    def build_context_messages(self, session: ChatSession) -> list[dict]:
        """
        Build context messages for AI API call
        
        Logic:
        - Always include system prompt
        - If summary exists: Include summary + recent messages
        - Else: Include all messages (up to a reasonable limit)
        
        Args:
            session: ChatSession object
        
        Returns:
            List of message dicts for AI API
        """
        messages = [
            {
                "role": "system",
                "content": "You are Mum Mentor, a caring and knowledgeable AI assistant helping mothers navigate pregnancy, parenting, and family life. Provide supportive, accurate, and practical advice in natural, conversational language. Write your responses as plain text without any markdown formatting - no asterisks, no bold text, no bullet points, no headers, no code blocks. Just write naturally as if you're having a warm, friendly conversation."
            }
        ]
        
        # Add summary if it exists
        if session.summary:
            messages.append({
                "role": "system",
                "content": f"Previous conversation summary: {session.summary}"
            })
            
            # Get only recent messages
            recent_messages = self.get_recent_messages(session.id, self.RECENT_MESSAGES_COUNT)
            logger.info(f"Using summary + recent messages | session_id={session.id} | recent_count={len(recent_messages)}")
        else:
            # Get all messages (or up to a limit)
            recent_messages = self.get_recent_messages(session.id, 100)
            logger.info(f"Using full history | session_id={session.id} | message_count={len(recent_messages)}")
        
        # Add conversation messages
        for msg in recent_messages:
            messages.append({
                "role": "user" if msg.sender == "user" else "assistant",
                "content": msg.message
            })
        
        return messages
    
    async def stream_ai_response(
        self,
        session: ChatSession,
        user_message_content: str
    ) -> AsyncGenerator[str, None]:
        """
        Stream AI response for a user message
        
        Args:
            session: ChatSession object
            user_message_content: The user's message content
        
        Yields:
            str: Chunks of AI response
        """
        # Build context including the new user message
        messages = self.build_context_messages(session)
        messages.append({
            "role": "user",
            "content": user_message_content
        })
        
        logger.info(f"Streaming AI response | session_id={session.id} | context_messages={len(messages)}")
        
        # Stream response from OpenRouter
        async for chunk in self.openrouter.stream_chat_completion(messages):
            yield chunk
    
    async def generate_title_background(self, session_id: UUID, first_message: str) -> None:
        """
        Background task to generate conversation title
        
        Args:
            session_id: UUID of the session
            first_message: First user message content
        """
        try:
            logger.info(f"Generating title | session_id={session_id}")
            
            title = await self.openrouter.generate_title(first_message)
            
            # Update session title
            session = self.db.query(ChatSession).filter(
                ChatSession.id == session_id
            ).first()
            
            if session and not session.title:
                session.title = title
                self.db.commit()
                logger.info(f"Title generated | session_id={session_id} | title={title}")
            
        except Exception as e:
            logger.error(f"Failed to generate title | session_id={session_id} | error={str(e)}")
            # Don't raise - title generation failure shouldn't affect the user
