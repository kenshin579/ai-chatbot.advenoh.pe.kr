"""블로그 문서 인덱싱 CLI

사용 예시:
    uv run python scripts/index_documents.py --blog-id blog-v2 --contents-dir ../../blog-v2.advenoh.pe.kr/contents/
    uv run python scripts/index_documents.py --blog-id investment --contents-dir ../../investment.advenoh.pe.kr/contents/
"""

import argparse
import sys
from pathlib import Path

# 프로젝트 루트를 import path에 추가
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.config import get_settings
from app.rag.chunker import split_documents
from app.rag.document_loader import load_blog_documents
from app.rag.embedder import create_embeddings
from app.rag.vector_store import VectorStoreManager


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

    settings = get_settings()

    print(f"[1/4] 문서 로딩: {args.contents_dir}")
    documents = load_blog_documents(args.contents_dir, args.blog_id)
    print(f"  -> {len(documents)}개 문서 로드 완료")

    print(f"[2/4] 청킹 (chunk_size={settings.chunk_size}, overlap={settings.chunk_overlap})")
    chunks = split_documents(documents, settings.chunk_size, settings.chunk_overlap)
    print(f"  -> {len(chunks)}개 청크 생성")

    print(f"[3/4] 벡터 저장소 연결: {settings.chroma_host}:{settings.chroma_port}")
    embeddings = create_embeddings(settings.embedding_model)
    manager = VectorStoreManager(settings.chroma_host, settings.chroma_port, embeddings)

    if args.reindex:
        print(f"  -> 기존 '{args.blog_id}' Collection 삭제")
        manager.delete_collection(args.blog_id)

    print(f"[4/4] '{args.blog_id}' Collection에 인덱싱 중...")
    indexed = manager.index_documents(args.blog_id, chunks)
    print(f"  -> {indexed}개 청크 인덱싱 완료!")


if __name__ == "__main__":
    main()
