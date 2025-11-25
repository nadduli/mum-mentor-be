"""
AI Chat Messaging Endpoint
Handles sending messages and streaming AI responses
"""

from fastapi import APIRouter, Depends, BackgroundTasks, status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from uuid import UUID
import json

from api.db.database import get_db, SessionLocal
from api.utils.deps import get_current_user
from api.v1.models.user.user import User
from api.v1.schemas.ai_chat import SendMessageRequest
from api.v1.services.chat_messaging_service import ChatMessagingService
from api.utils.responses import success_response
from api.utils.logger import logger


router = APIRouter(prefix="/chats", tags=["AI Chat"])


@router.post("/{session_id}/message")
async def send_message(
    session_id: UUID,
    request: SendMessageRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Send a message to AI and stream the response via Server-Sent Events (SSE)
    
    Flow:
    1. Verify session ownership
    2. Save user message to DB
    3. Generate title if first message (returned in 'start' event)
    4. Check if summarization needed (>50 messages)
    5. Stream AI response
    6. Save AI response after stream completes
    
    SSE Event Types:
    - start: Initial event with message_id and title (title only present for first message)
    - chunk: AI response content chunks
    - done: Stream completion with AI message_id
    - error: Error occurred during streaming
    
    Args:
        session_id: UUID of the chat session
        request: SendMessageRequest with message content
        background_tasks: FastAPI background tasks
        db: Database session
        current_user: Authenticated user
    
    Returns:
        StreamingResponse with Server-Sent Events
        First message returns: {"type": "start", "message_id": "...", "title": "Generated Title"}
        Subsequent messages: {"type": "start", "message_id": "..."}
    """
    try:
        logger.info(f"POST /chats/{session_id}/message | user_id={current_user.id}")
        
        messaging_service = ChatMessagingService(db)
        
        # Step 1: Verify session ownership
        session = messaging_service.get_session(session_id, current_user.id)
        
        # Step 2: Save user message immediately
        user_message = messaging_service.save_user_message(session_id, request.message)
        user_message_id = user_message.id
        
        # Step 3: Check message count for title generation
        message_count = messaging_service.get_message_count(session_id)
        
        generated_title = None
        if message_count == 1:  # First message in conversation
            logger.info(f"First message - generating title synchronously | session_id={session_id}")
            try:
                generated_title = await messaging_service.generate_title_background(session_id, request.message)
                logger.info(f"Title generated: {generated_title} | session_id={session_id}")
            except Exception as e:
                logger.error(f"Error generating title | session_id={session_id} | error={str(e)}")
                # Continue even if title generation fails
        
        # Step 4: Generate summary if needed (>50 messages)
        if message_count > ChatMessagingService.MESSAGE_SUMMARY_THRESHOLD:
            logger.info(f"Message count exceeds threshold - generating summary | session_id={session_id}")
            # Run synchronously to ensure summary is available for context
            await messaging_service.generate_summary_if_needed(session)
        
        # Get user message content for context
        user_message_content = request.message
        current_user_id = current_user.id
        
        # Step 5-6: Stream AI response
        async def event_generator():
            """Generate Server-Sent Events with AI response chunks"""
            accumulated_response = []
            
            # Create a new database session for the async generator
            stream_db = SessionLocal()
            
            try:
                # Send initial event with title (if first message)
                start_event = {'type': 'start', 'message_id': str(user_message_id)}
                if generated_title:
                    start_event['title'] = generated_title
                yield f"data: {json.dumps(start_event)}\n\n"
                
                # Get fresh session object for streaming
                stream_service = ChatMessagingService(stream_db)
                session_for_stream = stream_service.get_session(session_id, current_user_id)
                
                # Stream AI response chunks
                async for chunk in stream_service.stream_ai_response(session_for_stream, user_message_content):
                    accumulated_response.append(chunk)
                    yield f"data: {json.dumps({'type': 'chunk', 'content': chunk})}\n\n"
                
                # Save complete AI response to database
                full_response = "".join(accumulated_response)
                ai_message = stream_service.save_ai_message(session_id, full_response)
                
                # Send completion event
                yield f"data: {json.dumps({'type': 'done', 'message_id': str(ai_message.id)})}\n\n"
                
                logger.info(f"Message stream completed | session_id={session_id} | response_length={len(full_response)}")
                
            except Exception as e:
                logger.error(f"Error during streaming | session_id={session_id} | error={str(e)}")
                yield f"data: {json.dumps({'type': 'error', 'message': 'An error occurred'})}\n\n"
            finally:
                # Clean up the database session
                stream_db.close()
        
        return StreamingResponse(
            event_generator(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no"  # Disable nginx buffering
            }
        )
    
    except Exception as e:
        logger.error(f"Error in send_message | session_id={session_id} | error={str(e)}")
        raise
