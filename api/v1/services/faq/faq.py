import logging

from sqlalchemy import select, or_, func, String
from sqlalchemy.ext.asyncio import AsyncSession
from api.v1.models.faq.faq import FAQ

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

logger = logging.getLogger(__name__)

class FAQService:

    @staticmethod
    async def fetch_faqs(
            session: AsyncSession,
            category: str | None,
            search: str | None,
            limit: int,
            offset: int,
    ):
        logger.info(f"Fetching FAQs | category={category} | search={search} | limit={limit} | offset={offset}")

        query = select(FAQ).where(FAQ.is_published.is_(True))
        count_query = select(func.count(FAQ.id)).where(FAQ.is_published.is_(True))

        if category:
            query = query.where(FAQ.category.ilike(category))
            count_query = count_query.where(FAQ.category.ilike(category))

        if search:
            pattern = f"%{search}%"
            search_filter = or_(
                FAQ.question.ilike(pattern),
                FAQ.answer.ilike(pattern),
                FAQ.keywords.cast(String).ilike(pattern),
            )

            query = query.where(search_filter)
            count_query = count_query.where(search_filter)

        query = query.order_by(FAQ.order_index.asc())

        result = await session.execute(query.limit(limit).offset(offset))
        faqs = result.scalars().all()

        total = await session.scalar(count_query)

        logger.info(f"Fetched {len(faqs)} FAQs (total: {total})")

        return faqs, total