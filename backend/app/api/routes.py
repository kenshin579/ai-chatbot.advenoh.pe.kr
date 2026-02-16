from fastapi import APIRouter, Depends, HTTPException
from langchain_core.messages import AIMessage, HumanMessage

from app.api.models import (
    ChatRequest,
    ChatResponse,
    HealthResponse,
    IndexResponse,
    Source,
)
from app.config import Settings, get_settings
from app.rag.chain import create_rag_chain
from app.rag.chunker import split_documents
from app.rag.document_loader import load_blog_documents
from app.rag.embedder import create_embeddings
from app.rag.vector_store import VectorStoreManager

router = APIRouter()


def get_vector_store_manager(
    settings: Settings = Depends(get_settings),
) -> VectorStoreManager:
    embeddings = create_embeddings(settings.embedding_model)
    return VectorStoreManager(settings.chroma_host, settings.chroma_port, embeddings)


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

    return ChatResponse(answer=result["answer"], sources=sources)


@router.post("/index/{blog_id}", response_model=IndexResponse)
async def reindex(
    blog_id: str,
    settings: Settings = Depends(get_settings),
    manager: VectorStoreManager = Depends(get_vector_store_manager),
):
    """블로그 문서 전체 재인덱싱"""
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


@router.get("/health", response_model=HealthResponse)
async def health():
    return HealthResponse(status="ok")
