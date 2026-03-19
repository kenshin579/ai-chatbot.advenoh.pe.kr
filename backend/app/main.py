import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import router
from app.config import get_settings
from app.core.logging import init_logger
from app.db.connection import close_db, init_db
from app.middleware.request_logging import RequestLoggingMiddleware

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    init_logger(settings.log_level)
    logger.info("Application starting")

    if settings.mysql_password:
        await init_db(settings.database_url)
        logger.info("MySQL 연결 완료")
    else:
        logger.warning("MYSQL_PASSWORD 미설정 - DB 기능 비활성화")
    yield
    await close_db()


app = FastAPI(
    title="RAG Chatbot API",
    description="RAG 기반 블로그 Q&A 챗봇 API 서버",
    version="0.2.0",
    lifespan=lifespan,
)

app.add_middleware(RequestLoggingMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)
