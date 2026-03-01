# InspireMe 챗봇 - 구현 계획서

## 1. 프로젝트 구조 변경

### 1.1 ai-chatbot Backend 신규/수정 파일

```
backend/
├── app/
│   ├── api/
│   │   └── routes.py              # /index/{blog_id} 분기 추가 (inspireme)
│   ├── config.py                  # inspireme DB 설정 + blog_collections 추가
│   ├── prompts/
│   │   └── templates.py           # INSPIREME_SYSTEM_PROMPT 추가
│   └── rag/
│       ├── chain.py               # blog_id별 프롬프트 분기
│       └── inspireme_loader.py    # 신규: MySQL DB → Document 변환
├── scripts/
│   └── index_documents.py         # --blog-id inspireme 지원 추가
└── pyproject.toml                 # aiomysql 의존성 (이미 존재)
```

### 1.2 inspireme Frontend 신규/수정 파일

```
inspireme.advenoh.pe.kr/frontend/
├── components/
│   └── chatbot/                       # 신규 디렉토리
│       ├── ChatbotButton.tsx          # 플로팅 버튼
│       ├── ChatbotPanel.tsx           # 챗봇 패널 (메인 컨테이너)
│       ├── ChatMessageList.tsx        # 메시지 목록 + 피드백 버튼
│       └── ChatInput.tsx              # 입력 폼
├── lib/
│   └── chatbot-api.ts                 # 신규: ai-chatbot API 클라이언트
├── app/
│   └── layout.tsx                     # ChatbotButton 추가
└── next.config.ts                     # /api/chatbot/* 리라이트 추가
```

### 1.3 Charts 수정 파일

```
charts/charts/
├── ai-chatbot-be/
│   ├── values.yaml                    # inspireme MySQL 환경변수 추가
│   └── templates/configmap.yaml       # INSPIREME_MYSQL_* 환경변수 추가
└── gateway/values.yaml                # inspireme → ai-chatbot CORS 또는 라우트
```

---

## 2. ai-chatbot Backend 구현

### 2.1 설정 추가 (`app/config.py`)

```python
class Settings(BaseSettings):
    # 기존 설정...

    # 멀티 블로그 Collection 설정 — inspireme 추가
    blog_collections: dict[str, str] = {
        "blog-v2": "IT 블로그",
        "investment": "투자 블로그",
        "inspireme": "명언",
    }

    # inspireme DB 접속 정보 (인덱싱 시 사용)
    inspireme_mysql_host: str = "localhost"
    inspireme_mysql_port: int = 3306
    inspireme_mysql_database: str = "inspireme"
    inspireme_mysql_user: str = "inspireme"
    inspireme_mysql_password: str = ""

    @property
    def inspireme_database_url(self) -> str:
        return (
            f"mysql+aiomysql://{self.inspireme_mysql_user}:{quote_plus(self.inspireme_mysql_password)}"
            f"@{self.inspireme_mysql_host}:{self.inspireme_mysql_port}/{self.inspireme_mysql_database}"
        )
```

### 2.2 Document Loader 신규 (`app/rag/inspireme_loader.py`)

```python
import logging
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine
from langchain_core.documents import Document

logger = logging.getLogger(__name__)

QUOTES_QUERY = """
SELECT q.id, q.author, q.author_id, q.topics, q.tags,
       a.slug AS author_slug, a.birth_year, a.death_year, a.nationality,
       qt_ko.content AS content_ko, qt_en.content AS content_en,
       at_ko.name AS author_name_ko, at_en.name AS author_name_en,
       at_ko.bio AS author_bio_ko
FROM quotes q
LEFT JOIN authors a ON q.author_id = a.id
LEFT JOIN quote_translations qt_ko ON q.id = qt_ko.quote_id AND qt_ko.lang = 'ko'
LEFT JOIN quote_translations qt_en ON q.id = qt_en.quote_id AND qt_en.lang = 'en'
LEFT JOIN author_translations at_ko ON a.id = at_ko.author_id AND at_ko.lang = 'ko'
LEFT JOIN author_translations at_en ON a.id = at_en.author_id AND at_en.lang = 'en'
"""

AUTHORS_QUERY = """
SELECT a.id, a.slug, a.birth_year, a.death_year, a.nationality,
       at_ko.name AS name_ko, at_ko.bio AS bio_ko,
       at_en.name AS name_en, at_en.bio AS bio_en
FROM authors a
LEFT JOIN author_translations at_ko ON a.id = at_ko.author_id AND at_ko.lang = 'ko'
LEFT JOIN author_translations at_en ON a.id = at_en.author_id AND at_en.lang = 'en'
"""

BASE_URL = "https://inspireme.advenoh.pe.kr"


def _build_quote_document(row: dict) -> Document:
    """명언 DB 레코드를 LangChain Document로 변환한다."""
    content_parts = []
    if row.get("content_ko"):
        content_parts.append(f'"{row["content_ko"]}"')
    if row.get("content_en"):
        content_parts.append(f'"{row["content_en"]}"')

    author_name = row.get("author_name_ko") or row.get("author") or "Unknown"
    author_name_en = row.get("author_name_en") or ""
    if author_name_en:
        content_parts.append(f"— {author_name} ({author_name_en})")
    else:
        content_parts.append(f"— {author_name}")

    topics = row.get("topics") or []
    tags = row.get("tags") or []
    if topics:
        content_parts.append(f"주제: {', '.join(topics)}")
    if tags:
        content_parts.append(f"태그: {', '.join(tags)}")
    if row.get("author_bio_ko"):
        content_parts.append(f"저자 소개: {row['author_bio_ko']}")

    page_content = "\n".join(content_parts)

    metadata = {
        "blog_id": "inspireme",
        "type": "quote",
        "quote_id": row["id"],
        "author": author_name,
        "url": f"{BASE_URL}/quotes/{row['id']}",
    }
    if row.get("author_slug"):
        metadata["author_slug"] = row["author_slug"]
    if topics:
        metadata["topics"] = topics
    if tags:
        metadata["tags"] = tags

    return Document(page_content=page_content, metadata=metadata)


def _build_author_document(row: dict) -> Document:
    """저자 DB 레코드를 LangChain Document로 변환한다."""
    name_ko = row.get("name_ko") or "Unknown"
    name_en = row.get("name_en") or ""

    content_parts = []
    if name_en:
        content_parts.append(f"{name_ko} ({name_en})")
    else:
        content_parts.append(name_ko)

    if row.get("nationality"):
        content_parts.append(f"국적: {row['nationality']}")
    if row.get("birth_year"):
        birth = f"출생: {row['birth_year']}"
        if row.get("death_year"):
            birth += f", 사망: {row['death_year']}"
        content_parts.append(birth)
    if row.get("bio_ko"):
        content_parts.append(f"소개: {row['bio_ko']}")
    if row.get("bio_en"):
        content_parts.append(f"Bio: {row['bio_en']}")

    page_content = "\n".join(content_parts)

    metadata = {
        "blog_id": "inspireme",
        "type": "author",
        "author_id": row["id"],
        "author_slug": row.get("slug", ""),
        "url": f"{BASE_URL}/authors/{row.get('slug', '')}",
    }

    return Document(page_content=page_content, metadata=metadata)


async def load_inspireme_documents(database_url: str) -> list[Document]:
    """inspireme MySQL DB에서 명언/저자 데이터를 로드하여 Document 리스트로 반환한다."""
    engine = create_async_engine(database_url, pool_pre_ping=True)

    documents = []
    try:
        async with engine.connect() as conn:
            # 명언 로드
            result = await conn.execute(text(QUOTES_QUERY))
            rows = result.mappings().all()
            for row in rows:
                documents.append(_build_quote_document(dict(row)))
            logger.info(f"명언 {len(rows)}개 로드 완료")

            # 저자 로드
            result = await conn.execute(text(AUTHORS_QUERY))
            rows = result.mappings().all()
            for row in rows:
                documents.append(_build_author_document(dict(row)))
            logger.info(f"저자 {len(rows)}명 로드 완료")
    finally:
        await engine.dispose()

    logger.info(f"총 {len(documents)}개 Document 생성")
    return documents
```

### 2.3 인덱싱 엔드포인트 수정 (`app/api/routes.py`)

기존 `reindex` 함수의 contents_dirs 분기 로직에 inspireme 처리를 추가한다.

```python
from app.rag.inspireme_loader import load_inspireme_documents

@router.post("/index/{blog_id}", response_model=IndexResponse)
async def reindex(
    blog_id: str,
    _token: str = Depends(verify_index_token),
    settings: Settings = Depends(get_settings),
    manager: VectorStoreManager = Depends(get_vector_store_manager),
):
    if blog_id not in settings.blog_collections:
        raise HTTPException(status_code=400, detail=f"Unknown blog_id: {blog_id}")

    manager.delete_collection(blog_id)

    if blog_id == "inspireme":
        # DB에서 직접 로드 (청킹 불필요)
        documents = await load_inspireme_documents(settings.inspireme_database_url)
        indexed = manager.index_documents(blog_id, documents)
    else:
        # 기존: Markdown 파일 로드 + 청킹
        contents_dirs = {
            "blog-v2": "../../blog-v2.advenoh.pe.kr/contents/",
            "investment": "../../investment.advenoh.pe.kr/contents/",
        }
        contents_dir = contents_dirs.get(blog_id)
        if not contents_dir:
            raise HTTPException(status_code=400, detail=f"No contents directory for: {blog_id}")
        documents = load_blog_documents(contents_dir, blog_id)
        chunks = split_documents(documents, settings.chunk_size, settings.chunk_overlap)
        indexed = manager.index_documents(blog_id, chunks)

    return IndexResponse(status="ok", blog_id=blog_id, indexed_chunks=indexed)
```

### 2.4 inspireme 전용 프롬프트 (`app/prompts/templates.py`)

```python
# 기존 SYSTEM_PROMPT 아래에 추가

INSPIREME_SYSTEM_PROMPT = """당신은 명언 추천 전문 AI 어시스턴트입니다.
사용자의 질문에 맞는 명언을 추천하고, 저자 정보를 안내합니다.

## 답변 스타일

- **공감과 추천**: 사용자의 감정이나 상황에 공감하며 적절한 명언을 추천하세요.
- **원문 인용**: 명언을 인용할 때는 검색된 원문을 그대로 사용하세요.
- **출처 명시**: 저자 이름을 반드시 함께 제공하세요.

## 답변 규칙

1. **근거 기반**: 반드시 컨텍스트에 포함된 명언만 추천하세요. 검색 결과에 없는 명언을 지어내지 마세요.
2. **정보 없음 처리**: 관련 명언을 찾지 못한 경우 "관련 명언을 찾지 못했습니다."라고 답변하세요.
3. **다국어**: 한국어로 답변하되, 영어 원문이 있으면 함께 제공하세요.
4. **간결함**: 핵심을 중심으로 간결하게 답변하세요.

## 컨텍스트

{context}"""
```

### 2.5 체인 프롬프트 분기 (`app/rag/chain.py`)

```python
from app.prompts.templates import SYSTEM_PROMPT, INSPIREME_SYSTEM_PROMPT

def create_rag_chain(
    vector_store: Chroma,
    model: str,
    top_k: int = 5,
    retriever: RetrieverLike | None = None,
    blog_id: str | None = None,         # 신규 파라미터
):
    llm = ChatOpenAI(model=model, temperature=0)

    if retriever is None:
        retriever = vector_store.as_retriever(search_kwargs={"k": top_k})

    # 대화 히스토리를 고려한 질문 재작성 체인 (기존 동일)
    contextualize_prompt = ChatPromptTemplate.from_messages([
        ("system", "대화 히스토리와 최신 사용자 질문을 고려하여, "
         "대화 히스토리 없이도 이해할 수 있는 독립적인 질문으로 재작성하세요. "
         "질문을 답변하지 마세요. 재작성이 필요 없으면 그대로 반환하세요."),
        MessagesPlaceholder("chat_history"),
        ("human", "{input}"),
    ])
    history_aware_retriever = create_history_aware_retriever(
        llm, retriever, contextualize_prompt
    )

    # blog_id에 따라 프롬프트 분기
    system_prompt = INSPIREME_SYSTEM_PROMPT if blog_id == "inspireme" else SYSTEM_PROMPT

    qa_prompt = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        MessagesPlaceholder("chat_history"),
        ("human", "{input}"),
    ])
    question_answer_chain = create_stuff_documents_chain(llm, qa_prompt)

    return create_retrieval_chain(history_aware_retriever, question_answer_chain)
```

### 2.6 routes.py 호출부 수정

```python
# /chat 엔드포인트에서 blog_id를 create_rag_chain에 전달
chain = create_rag_chain(store, settings.openai_model, settings.top_k, blog_id=request.blog_id)
```

---

## 3. inspireme Frontend 구현

### 3.1 Next.js 리라이트 추가 (`next.config.ts`)

```typescript
async rewrites() {
    const backendUrl = process.env.BACKEND_URL || "http://localhost:8080";
    const chatbotUrl = process.env.CHATBOT_API_URL || "http://localhost:8080";
    return [
      {
        source: "/api/:path*",
        destination: `${backendUrl}/api/:path*`,
      },
      {
        source: "/chatbot-api/:path*",
        destination: `${chatbotUrl}/:path*`,
      },
    ];
},
```

### 3.2 API 클라이언트 (`lib/chatbot-api.ts`)

```typescript
export interface ChatMessage {
  role: "human" | "ai";
  content: string;
}

export interface Source {
  title: string;
  url: string;
}

export interface ChatResponse {
  answer: string;
  sources: Source[];
  message_id: string;
}

export interface FeedbackRequest {
  message_id: string;
  blog_id: string;
  question: string;
  rating: "up" | "down";
}

const BASE_URL = "/chatbot-api";

export async function sendChat(
  question: string,
  chatHistory: ChatMessage[] = [],
): Promise<ChatResponse> {
  const res = await fetch(`${BASE_URL}/chat`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      blog_id: "inspireme",
      question,
      chat_history: chatHistory,
    }),
  });
  if (!res.ok) {
    const error = await res.json().catch(() => ({}));
    throw new Error(error.detail || `HTTP ${res.status}`);
  }
  return res.json();
}

export async function sendFeedback(request: FeedbackRequest): Promise<void> {
  await fetch(`${BASE_URL}/feedback`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(request),
  });
}
```

### 3.3 ChatbotButton (`components/chatbot/ChatbotButton.tsx`)

- 우측 하단 고정 위치 (`fixed bottom-6 right-6`)
- `MessageCircle` 아이콘 (lucide-react)
- 클릭 시 ChatbotPanel 토글
- z-index: 50

### 3.4 ChatbotPanel (`components/chatbot/ChatbotPanel.tsx`)

- 우측 하단 400×500px 패널 (`fixed bottom-20 right-6`)
- 헤더: "명언 AI 도우미" + 닫기 버튼 (X)
- 메시지 상태 관리 (messages, isLoading, error)
- chat_history 구성하여 sendChat 호출
- ChatMessageList + ChatInput 합성

### 3.5 ChatMessageList (`components/chatbot/ChatMessageList.tsx`)

- ScrollArea로 감싸고 자동 스크롤
- 사용자 메시지: 우측 파란색 (`bg-primary text-primary-foreground`)
- AI 메시지: 좌측 회색 (`bg-muted`)
- 출처 링크: `/quotes/{id}`로 이동
- 👍👎 피드백 버튼 (sendFeedback 호출)
- 로딩 상태: "답변을 생성하고 있습니다..." 펄스 애니메이션
- 초기 상태: 추천 질문 예시 표시

### 3.6 ChatInput (`components/chatbot/ChatInput.tsx`)

- Input + Send 버튼
- 엔터 키 제출
- 로딩 중 비활성화
- placeholder: "명언에 대해 질문해 보세요..."

### 3.7 Root Layout에 ChatbotButton 추가

```typescript
// app/layout.tsx
import { ChatbotButton } from "@/components/chatbot/ChatbotButton";

// layout return 부분에 추가
<ChatbotButton />
```

---

## 4. Charts 변경

### 4.1 ai-chatbot-be 환경변수 추가 (`charts/ai-chatbot-be/values.yaml`)

```yaml
config:
  # 기존 설정...
  inspiremeMysqlHost: "mysql-headless.app.svc.cluster.local"
  inspiremeMysqlPort: "3306"
  inspiremeMysqlDatabase: "inspireme"

secrets:
  # 기존 설정...
  inspiremeMysql:
    user: "inspireme"
    password: "<비밀번호>"
```

### 4.2 ConfigMap 환경변수 추가 (`charts/ai-chatbot-be/templates/configmap.yaml`)

- `INSPIREME_MYSQL_HOST`, `INSPIREME_MYSQL_PORT`, `INSPIREME_MYSQL_DATABASE`

### 4.3 Secret 환경변수 추가 (`charts/ai-chatbot-be/templates/secret.yaml`)

- `INSPIREME_MYSQL_USER`, `INSPIREME_MYSQL_PASSWORD`

### 4.4 inspireme-fe 환경변수 추가 (`charts/inspireme-fe/values.yaml`)

```yaml
config:
  chatbotApiUrl: "http://ai-chatbot-be-service:80"
```

---

## 5. 테스트

### 5.1 Backend 단위 테스트

- `test_inspireme_loader.py`: _build_quote_document, _build_author_document 변환 정확성
- `test_inspireme_loader.py`: 다국어 번역 포함 여부 + 빈 번역 fallback
- `test_api.py`: POST /index/inspireme 정상 동작
- `test_api.py`: POST /chat { blog_id: "inspireme" } 정상 응답

### 5.2 E2E 테스트 (MCP Playwright)

- inspireme 사이트에서 플로팅 버튼 표시 확인
- 버튼 클릭 → 챗봇 패널 열림 확인
- 질문 입력 → 답변 표시 확인
- 출처 링크 클릭 → 명언 상세 페이지 이동 확인
- 👍👎 피드백 버튼 클릭 확인
