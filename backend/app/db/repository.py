import logging

from sqlalchemy import case, func, select, text
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

    async def get_daily_counts(self, days: int = 7) -> list[dict]:
        """최근 N일 일별 질문 수"""
        result = await self.session.execute(
            text(
                "SELECT DATE(created_at) as date, COUNT(*) as count "
                "FROM query_logs "
                "WHERE created_at >= DATE_SUB(NOW(), INTERVAL :days DAY) "
                "GROUP BY DATE(created_at) "
                "ORDER BY date ASC"
            ),
            {"days": days},
        )
        return [{"date": str(row.date), "count": row.count} for row in result]

    async def get_top_questions(self, limit: int = 10) -> list[dict]:
        """인기 질문 TOP N"""
        stmt = (
            select(QueryLog.question, func.count().label("count"))
            .group_by(QueryLog.question)
            .order_by(func.count().desc())
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        return [{"question": row.question, "count": row.count} for row in result]

    async def get_feedback_ratio(self) -> dict:
        """👍👎 비율"""
        stmt = select(
            func.count().label("total"),
            func.sum(case((Feedback.rating == "up", 1), else_=0)).label("up_count"),
            func.sum(case((Feedback.rating == "down", 1), else_=0)).label("down_count"),
        )
        result = await self.session.execute(stmt)
        row = result.one()
        total = row.total or 0
        up = int(row.up_count or 0)
        down = int(row.down_count or 0)
        return {
            "total": total,
            "up": up,
            "down": down,
            "up_ratio": round(up / total, 2) if total > 0 else 0.0,
        }

    async def get_avg_response_time(self) -> float:
        """평균 응답 시간 (ms)"""
        stmt = select(func.avg(QueryLog.response_time_ms)).where(
            QueryLog.response_time_ms.is_not(None)
        )
        result = await self.session.execute(stmt)
        avg = result.scalar()
        return round(float(avg), 1) if avg else 0.0

    async def get_search_failure_rate(self) -> float:
        """검색 실패율 (has_results=false 비율)"""
        stmt = select(
            func.count().label("total"),
            func.sum(case((QueryLog.has_results == False, 1), else_=0)).label("failed"),  # noqa: E712
        )
        result = await self.session.execute(stmt)
        row = result.one()
        total = row.total or 0
        failed = int(row.failed or 0)
        return round(failed / total, 2) if total > 0 else 0.0
