import logging
from typing import Optional

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from api.v1.models.user.user import FAQ
from api.utils.logger import logger


class FAQService:
    """Service class for FAQ-related operations"""

    @staticmethod
    def fetch_faqs(
        session: Session,
        category: Optional[str],
        search: Optional[str],
        limit: int,
        offset: int,
    ):

        try:
            logger.info(
                "Fetching FAQs | category=%s | search=%s | limit=%s | offset=%s",
                category, search, limit, offset
            )

            faqs, total = FAQ.fetch_all(
                db_session=session,
                category=category,
                search=search,
                limit=limit,
                offset=offset
            )

            # Run queries
            result = session.execute(query)
            faqs = result.scalars().all()

            total = session.scalar(count_query)

            logger.info("Fetched %s FAQs (total=%s)", len(faqs), total)

            return faqs, None, total

        except SQLAlchemyError as db_err:
            session.rollback()
            logger.error("Database error while fetching FAQs: %s", str(db_err), exc_info=True)
            return None, "A database error occurred while fetching FAQs", None

        except Exception as e:
            session.rollback()
            logger.error("Unexpected error fetching FAQs: %s", str(e), exc_info=True)
            return None, "An unexpected error occurred while fetching FAQs", None