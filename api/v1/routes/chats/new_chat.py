"""
New Chat Session Route
Creates a new chat session and optionally adds the first message
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
import uuid

from api.db.database import get_db
from api.utils.deps import get_current_user
from api.v1.models.user.user import User
from api.v1.schemas.chat import ChatSessionCreate, ChatSessionResponse
from api.v1.services.chat_service import create_new_chat_session
from api.utils.responses import success_response
from api.utils.logger import logger


chat_router = APIRouter(prefix="/chats", tags=["Chat"])


@chat_router.post(
    "/new",
    status_code=status.HTTP_201_CREATED,
    summary="Create New Chat Session",
    response_description="New chat session created successfully",
    responses={
        201: {"description": "Chat session created successfully"},
        400: {"description": "Invalid request data"},
        401: {"description": "Unauthorized - User not authenticated"},
        500: {"description": "Internal server error"}
    }
)
def create_new_chat(
    chat_data: ChatSessionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Create a new chat session.
    
    This endpoint initializes a new conversation/chat session. It automatically generates
    a title from the user's initial message (similar to ChatGPT). The session is saved to
    the database and linked to the authenticated user.
    
    How it works:
    - The client sends the first message they want to discuss
    - We generate a meaningful title from that message (e.g., first 50-100 characters)
    - A new ChatSession is created and saved to the database
    - The session ID is returned so the client can use it for future messages
    
    How to test in Swagger:
    1. Click the Authorize button at the top of Swagger
    2. Paste your access token in this format:
       Bearer <your_token_here>
    3. Execute the /chats/new endpoint with a message
    
    Example request:
    ```json
    {
        "message": "I'm pregnant and experiencing morning sickness, what should I eat?"
    }
    ```
    """
    try:
        logger.info(f"Creating new chat session for user: {current_user.id}")
        
        # Create the chat session
        session, error = create_new_chat_session(
            db=db,
            user_id=current_user.id,
            initial_message=chat_data.message
        )
        
        if error:
            logger.error(f"Failed to create chat session: {error}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=error
            )
        
        # Prepare response
        response_data = ChatSessionResponse(
            id=str(session.id),
            user_id=str(session.user_id),
            title=session.title,
            created_at=session.created_at
        )
        
        logger.info(f"Chat session created successfully: {session.id}")
        
        return success_response(
            data=response_data.model_dump(),
            message="Chat session created successfully",
            status_code=status.HTTP_201_CREATED
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error creating chat session: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred while creating the chat session"
        )
