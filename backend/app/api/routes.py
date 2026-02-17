import logging
import time
import uuid

from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from langchain_core.messages import AIMessage, HumanMessage
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.models import (
    ChatRequest,
    ChatResponse,
    FeedbackRequest,
    FeedbackResponse,
    HealthResponse,
    IndexResponse,
    Source,
)
from app.config import Settings, get_settings
import app.db.connection as db_conn
from app.db.connection import get_session
from app.db.repository import QueryLogRepository
from app.rag.chain import create_rag_chain
from app.rag.chunker import split_documents
from app.rag.document_loader import load_blog_documents
from app.rag.embedder import create_embeddings
from app.rag.vector_store import VectorStoreManager

logger = logging.getLogger(__name__)

router = APIRouter()
bearer_scheme = HTTPBearer()


def get_vector_store_manager(
    settings: Settings = Depends(get_settings),
) -> VectorStoreManager:
    embeddings = create_embeddings(settings.embedding_model)
    return VectorStoreManager(settings.chroma_host, settings.chroma_port, embeddings)


def verify_index_token(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    settings: Settings = Depends(get_settings),
) -> str:
    """인덱싱 API의 Bearer 토큰을 검증한다."""
    if not settings.rag_index_token:
        raise HTTPException(status_code=500, detail="RAG_INDEX_TOKEN not configured")
    if credentials.credentials != settings.rag_index_token:
        raise HTTPException(status_code=401, detail="Invalid token")
    return credentials.credentials


@router.post("/chat", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    settings: Settings = Depends(get_settings),
    manager: VectorStoreManager = Depends(get_vector_store_manager),
):
    """RAG 기반 Q&A - blog_id로 Collection 선택"""
    if request.blog_id not in settings.blog_collections:
        raise HTTPException(
            status_code=400, detail=f"Unknown blog_id: {request.blog_id}"
        )

    start_time = time.time()
    message_id = str(uuid.uuid4())

    store = manager.get_store(request.blog_id)
    chain = create_rag_chain(store, settings.openai_model, settings.top_k)

    # chat_history를 LangChain 메시지 형식으로 변환
    chat_history = []
    if request.chat_history:
        for msg in request.chat_history:
            if msg.role == "human":
                chat_history.append(HumanMessage(content=msg.content))
            else:
                chat_history.append(AIMessage(content=msg.content))

    result = chain.invoke({
        "input": request.question,
        "chat_history": chat_history,
    })

    # 소스 문서에서 중복 제거하여 출처 생성
    seen_urls = set()
    sources = []
    for doc in result.get("context", []):
        url = doc.metadata.get("url", "")
        title = doc.metadata.get("title", "")
        if url and url not in seen_urls:
            seen_urls.add(url)
            sources.append(Source(title=title, url=url))

    response_time_ms = int((time.time() - start_time) * 1000)

    # 쿼리 로그 저장
    if db_conn.async_session_factory:
        try:
            async with db_conn.async_session_factory() as session:
                repo = QueryLogRepository(session)
                await repo.save_query_log(
                    message_id=message_id,
                    blog_id=request.blog_id,
                    question=request.question,
                    answer=result["answer"],
                    sources=[s.model_dump() for s in sources],
                    response_time_ms=response_time_ms,
                    has_results=len(sources) > 0,
                )
        except Exception:
            logger.exception("쿼리 로그 저장 실패")

    return ChatResponse(
        answer=result["answer"],
        sources=sources,
        message_id=message_id,
    )


@router.post("/index/{blog_id}", response_model=IndexResponse)
async def reindex(
    blog_id: str,
    _token: str = Depends(verify_index_token),
    settings: Settings = Depends(get_settings),
    manager: VectorStoreManager = Depends(get_vector_store_manager),
):
    """블로그 문서 전체 재인덱싱 (Bearer 토큰 인증 필요)"""
    if blog_id not in settings.blog_collections:
        raise HTTPException(
            status_code=400, detail=f"Unknown blog_id: {blog_id}"
        )

    contents_dirs = {
        "blog-v2": "../../blog-v2.advenoh.pe.kr/contents/",
        "investment": "../../investment.advenoh.pe.kr/contents/",
    }
    contents_dir = contents_dirs.get(blog_id)
    if not contents_dir:
        raise HTTPException(
            status_code=400, detail=f"No contents directory for: {blog_id}"
        )

    # 기존 Collection 삭제 후 재인덱싱
    manager.delete_collection(blog_id)
    documents = load_blog_documents(contents_dir, blog_id)
    chunks = split_documents(documents, settings.chunk_size, settings.chunk_overlap)
    indexed = manager.index_documents(blog_id, chunks)

    return IndexResponse(status="ok", blog_id=blog_id, indexed_chunks=indexed)


@router.post("/feedback", response_model=FeedbackResponse)
async def feedback(
    request: FeedbackRequest,
    settings: Settings = Depends(get_settings),
):
    """사용자 피드백 저장 및 LangSmith 연동"""
    # feedbacks 테이블 저장
    if db_conn.async_session_factory:
        try:
            async with db_conn.async_session_factory() as session:
                repo = QueryLogRepository(session)
                await repo.save_feedback(
                    message_id=request.message_id,
                    blog_id=request.blog_id,
                    question=request.question,
                    rating=request.rating,
                )
        except Exception:
            logger.exception("피드백 저장 실패")

    # LangSmith 피드백 전송 (API key가 설정된 경우)
    if settings.langsmith_api_key:
        try:
            from langsmith import Client
            ls_client = Client(api_key=settings.langsmith_api_key)
            ls_client.create_feedback(
                run_id=request.message_id,
                key="user_feedback",
                score=1.0 if request.rating == "up" else 0.0,
                comment=request.question,
            )
        except Exception:
            logger.exception("LangSmith 피드백 전송 실패")

    return FeedbackResponse(status="ok")


@router.get("/admin/stats")
async def admin_stats():
    """Admin 대시보드 통계 데이터 반환"""
    if not db_conn.async_session_factory:
        return {
            "daily_queries": [],
            "top_questions": [],
            "feedback_score": {"total": 0, "up": 0, "down": 0, "up_ratio": 0.0},
            "avg_response_time": 0.0,
            "search_failure_rate": 0.0,
        }

    async with db_conn.async_session_factory() as session:
        repo = QueryLogRepository(session)
        daily_queries, top_questions, feedback_score, avg_response_time, search_failure_rate = (
            await repo.get_daily_counts(),
            await repo.get_top_questions(),
            await repo.get_feedback_ratio(),
            await repo.get_avg_response_time(),
            await repo.get_search_failure_rate(),
        )

    return {
        "daily_queries": daily_queries,
        "top_questions": top_questions,
        "feedback_score": feedback_score,
        "avg_response_time": avg_response_time,
        "search_failure_rate": search_failure_rate,
    }


@router.get("/health", response_model=HealthResponse)
async def health():
    return HealthResponse(status="ok")
