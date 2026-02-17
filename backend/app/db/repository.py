import logging

from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Feedback, QueryLog

logger = logging.getLogger(__name__)


class QueryLogRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def save_query_log(
        self,
        message_id: str,
        blog_id: str,
        question: str,
        answer: str,
        sources: list[dict] | None = None,
        response_time_ms: int | None = None,
        has_results: bool | None = None,
    ) -> None:
        log = QueryLog(
            message_id=message_id,
            blog_id=blog_id,
            question=question,
            answer=answer,
            sources=sources,
            response_time_ms=response_time_ms,
            has_results=has_results,
        )
        self.session.add(log)
        await self.session.commit()

    async def save_feedback(
        self,
        message_id: str,
        blog_id: str,
        question: str,
        rating: str,
    ) -> None:
        fb = Feedback(
            message_id=message_id,
            blog_id=blog_id,
            question=question,
            rating=rating,
        )
        self.session.add(fb)
        await self.session.commit()
