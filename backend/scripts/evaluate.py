"""RAG 평가 실행 스크립트.

사용 예시:
    uv run python scripts/evaluate.py --blog-id blog-v2
"""

import argparse
import json
import logging
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.config import get_settings
from app.core.logging import init_logger
from app.evaluation.dataset import EVAL_DATASET
from app.evaluation.evaluator import run_evaluation
from app.rag.chain import create_rag_chain
from app.rag.embedder import create_embeddings
from app.rag.vector_store import VectorStoreManager

logger = logging.getLogger(__name__)


def main():
    parser = argparse.ArgumentParser(description="RAG 평가 실행")
    parser.add_argument(
        "--blog-id",
        default="blog-v2",
        choices=["blog-v2", "investment"],
        help="평가할 블로그 ID",
    )
    parser.add_argument(
        "--output",
        default=None,
        help="결과 저장 경로 (JSON)",
    )
    args = parser.parse_args()

    init_logger()
    settings = get_settings()
    embeddings = create_embeddings(settings.embedding_model)
    manager = VectorStoreManager(settings.chroma_host, settings.chroma_port, embeddings)
    store = manager.get_store(args.blog_id)

    # 평가 데이터셋 필터링
    eval_items = [item for item in EVAL_DATASET if item["blog_id"] == args.blog_id]
    if not eval_items:
        logger.info("평가 데이터 없음", extra={"blog_id": args.blog_id})
        return

    logger.info("평가 시작", extra={"blog_id": args.blog_id, "question_count": len(eval_items)})

    # RAG 체인으로 각 질문에 대한 답변 생성
    chain = create_rag_chain(store, settings.openai_model, settings.top_k)

    questions = []
    answers = []
    contexts = []
    ground_truths = []

    for i, item in enumerate(eval_items):
        logger.info("질문 처리 중", extra={"progress": f"{i + 1}/{len(eval_items)}", "question": item["question"]})
        result = chain.invoke({
            "input": item["question"],
            "chat_history": [],
        })
        questions.append(item["question"])
        answers.append(result["answer"])
        contexts.append([doc.page_content for doc in result.get("context", [])])
        ground_truths.append(item["ground_truth"])

    # RAGAS 평가 실행
    logger.info("RAGAS 평가 실행 중")
    scores = run_evaluation(questions, answers, contexts, ground_truths)

    # 결과 출력
    for metric, score in scores.items():
        if isinstance(score, (int, float)):
            logger.info("평가 결과", extra={"metric": metric, "score": round(score, 4)})

    # JSON 저장
    if args.output:
        output_path = Path(args.output)
        output_path.write_text(json.dumps(scores, indent=2, ensure_ascii=False))
        logger.info("결과 저장 완료", extra={"path": str(output_path)})


if __name__ == "__main__":
    main()
