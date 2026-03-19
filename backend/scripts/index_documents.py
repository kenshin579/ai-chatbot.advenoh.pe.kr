"""블로그 문서 인덱싱 CLI

사용 예시:
    uv run python scripts/index_documents.py --blog-id blog-v2 --contents-dir ../../blog-v2.advenoh.pe.kr/contents/
    uv run python scripts/index_documents.py --blog-id investment --contents-dir ../../investment.advenoh.pe.kr/contents/
"""

import argparse
import logging
import os
import sys
from pathlib import Path

# 프로젝트 루트를 import path에 추가
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

# AI_CHATBOT_OPEN_API_KEY 환경 변수를 OPENAI_API_KEY로 매핑
if 'AI_CHATBOT_OPEN_API_KEY' in os.environ:
    os.environ['OPENAI_API_KEY'] = os.environ['AI_CHATBOT_OPEN_API_KEY']

from app.config import get_settings
from app.core.logging import init_logger
from app.rag.chunker import split_documents
from app.rag.document_loader import load_blog_documents
from app.rag.embedder import create_embeddings
from app.rag.vector_store import VectorStoreManager

logger = logging.getLogger(__name__)


def main():
    parser = argparse.ArgumentParser(description="블로그 문서 인덱싱")
    parser.add_argument(
        "--blog-id",
        required=True,
        choices=["blog-v2", "investment"],
        help="인덱싱할 블로그 ID",
    )
    parser.add_argument(
        "--contents-dir",
        required=True,
        help="블로그 contents/ 디렉토리 경로",
    )
    parser.add_argument(
        "--reindex",
        action="store_true",
        help="기존 Collection 삭제 후 재인덱싱",
    )
    args = parser.parse_args()

    init_logger()
    settings = get_settings()

    logger.info("[1/4] 문서 로딩", extra={"contents_dir": args.contents_dir})
    documents = load_blog_documents(args.contents_dir, args.blog_id)
    logger.info("문서 로드 완료", extra={"count": len(documents)})

    logger.info("[2/4] 청킹", extra={"chunk_size": settings.chunk_size, "overlap": settings.chunk_overlap})
    chunks = split_documents(documents, settings.chunk_size, settings.chunk_overlap)
    logger.info("청크 생성 완료", extra={"count": len(chunks)})

    logger.info("[3/4] 벡터 저장소 연결", extra={"host": settings.chroma_host, "port": settings.chroma_port})
    embeddings = create_embeddings(settings.embedding_model)
    manager = VectorStoreManager(settings.chroma_host, settings.chroma_port, embeddings)

    if args.reindex:
        logger.info("기존 Collection 삭제", extra={"blog_id": args.blog_id})
        manager.delete_collection(args.blog_id)

    logger.info("[4/4] 인덱싱 시작", extra={"blog_id": args.blog_id})
    indexed = manager.index_documents(args.blog_id, chunks)
    logger.info("인덱싱 완료", extra={"blog_id": args.blog_id, "indexed_chunks": indexed})


if __name__ == "__main__":
    main()
