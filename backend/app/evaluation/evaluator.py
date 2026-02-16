"""RAGAS 기반 RAG 평가 모듈.

Faithfulness, Answer Relevancy, Context Precision 메트릭을 측정한다.
"""

from ragas import evaluate
from ragas.dataset_schema import EvaluationDataset, SingleTurnSample
from ragas.metrics import (
    AnswerRelevancy,
    ContextPrecision,
    Faithfulness,
)


def create_evaluation_dataset(
    questions: list[str],
    answers: list[str],
    contexts: list[list[str]],
    ground_truths: list[str],
) -> EvaluationDataset:
    """RAGAS 평가 데이터셋을 생성한다."""
    samples = []
    for q, a, ctx, gt in zip(questions, answers, contexts, ground_truths):
        samples.append(
            SingleTurnSample(
                user_input=q,
                response=a,
                retrieved_contexts=ctx,
                reference=gt,
            )
        )
    return EvaluationDataset(samples=samples)


def run_evaluation(
    questions: list[str],
    answers: list[str],
    contexts: list[list[str]],
    ground_truths: list[str],
) -> dict:
    """RAGAS 평가를 실행하고 결과를 반환한다.

    Returns:
        dict: 각 메트릭 이름과 점수를 담은 딕셔너리
    """
    dataset = create_evaluation_dataset(questions, answers, contexts, ground_truths)

    metrics = [
        Faithfulness(),
        AnswerRelevancy(),
        ContextPrecision(),
    ]

    result = evaluate(dataset=dataset, metrics=metrics)
    return dict(result)
