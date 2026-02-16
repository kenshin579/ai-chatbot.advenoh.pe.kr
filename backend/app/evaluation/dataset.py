"""RAG 평가용 데이터셋.

각 항목은 질문, 기대 답변(ground_truth), 대상 blog_id로 구성된다.
RAGAS 평가 시 이 데이터셋을 기반으로 Faithfulness, Answer Relevancy,
Context Precision을 측정한다.
"""

EVAL_DATASET = [
    {
        "question": "Go에서 goroutine이란 무엇인가요?",
        "ground_truth": "goroutine은 Go 런타임이 관리하는 경량 스레드로, go 키워드를 사용하여 함수를 동시에 실행할 수 있다.",
        "blog_id": "blog-v2",
    },
    {
        "question": "Go에서 iota는 어떻게 사용하나요?",
        "ground_truth": "iota는 Go의 const 선언에서 사용하는 predefined identifier로, 연속적인 정수 상수 0, 1, 2, ...를 나타낸다.",
        "blog_id": "blog-v2",
    },
    {
        "question": "Java에서 Stream API의 주요 특징은?",
        "ground_truth": "Java Stream API는 컬렉션 데이터를 함수형 스타일로 처리할 수 있는 API로, filter, map, reduce 등의 연산을 체이닝할 수 있다.",
        "blog_id": "blog-v2",
    },
    {
        "question": "Docker와 컨테이너의 차이점은?",
        "ground_truth": "Docker는 컨테이너를 생성하고 관리하는 플랫폼이고, 컨테이너는 애플리케이션과 그 의존성을 격리하여 실행하는 가상화 기술이다.",
        "blog_id": "blog-v2",
    },
    {
        "question": "Git rebase와 merge의 차이는?",
        "ground_truth": "merge는 두 브랜치의 히스토리를 합치는 커밋을 만들고, rebase는 한 브랜치의 커밋을 다른 브랜치 위에 재배치하여 선형 히스토리를 만든다.",
        "blog_id": "blog-v2",
    },
]
