from sqlalchemy.orm import Session
from api.v1.models.chat_session import ChatSession
import uuid

class ChatService:
    @staticmethod
    def delete_conversation(session: Session, conversation_id: uuid.UUID, user_id: uuid.UUID) -> bool:
        """
        Deletes a chat session only if it exists AND belongs to the user.
        Returns True if deleted, False if not found/unauthorized.
        """
        chat_session = ChatSession.fetch_one(session, id=conversation_id, user_id=user_id)

        if not chat_session:
            return False

        chat_session.delete(session)
        
        return True