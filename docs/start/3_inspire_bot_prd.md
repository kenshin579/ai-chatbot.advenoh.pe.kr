# InspireMe 챗봇 - 프로젝트 PRD

## 1. 개요

### 1.1 목적

`inspireme.advenoh.pe.kr` 사이트에 AI 챗봇을 추가하여 사용자가 명언 추천/검색, 저자 정보 조회를 자연어로 할 수 있도록 한다. 기존 `ai-chatbot.advenoh.pe.kr` 백엔드의 RAG 파이프라인에 inspireme 데이터 소스를 추가하고, inspireme 프론트엔드에 챗봇 UI를 임베드한다.

### 1.2 선행 조건

- `ai-chatbot.advenoh.pe.kr` API 서버 배포 완료 (`6_chatbot_project_prd.md`)
- `inspireme.advenoh.pe.kr` 백엔드/프론트엔드 배포 완료
- ChromaDB 서버 운영 중
- MySQL에 inspireme DB (quotes, authors 테이블) 데이터 존재

### 1.3 관련 Repo

- **ai-chatbot**: [ai-chatbot.advenoh.pe.kr](https://github.com/kenshin579/ai-chatbot.advenoh.pe.kr) — Backend (FastAPI), Frontend (Next.js)
- **inspireme**: [inspireme.advenoh.pe.kr](https://github.com/kenshin579/inspireme.advenoh.pe.kr) — Backend (Go/Echo), Frontend (Next.js)

---

## 2. 핵심 도전과제

기존 ai-chatbot의 RAG 파이프라인은 **마크다운 파일** 기반이다. inspireme 데이터를 지원하려면 다음 차이점을 해결해야 한다.

| 항목 | 기존 (blog-v2) | inspireme |
|------|---------------|-----------|
| 데이터 소스 | Markdown 파일 (`contents/index.md`) | MySQL DB (quotes, authors 테이블) |
| 문서 크기 | 블로그 글 (수백~수천 자) | 명언 1-2문장 (10~100자) |
| 청킹 전략 | `chunk_size=1000`, Markdown 구분자 기반 | 청킹 불필요 (명언 1개 = 1 Document) |
| 메타데이터 | frontmatter (title, date, category, tags) | author, topics, tags, language |
| 다국어 | 단일 언어 콘텐츠 | ko/en 번역 테이블 (quote_translations, author_translations) |
| 인덱싱 트리거 | GitHub Actions (contents/ 변경 시) | API 호출 또는 스케줄 (DB 변경 시) |
| URL 연결 | 블로그 포스트 URL | inspireme 명언 상세 페이지 URL |

---

## 3. 핵심 기능

1. **API → Document 변환**: inspireme 백엔드 API에서 명언/저자 데이터를 가져와 LangChain Document로 변환하여 ChromaDB에 인덱싱
2. **명언 특화 RAG**: 짧은 텍스트에 최적화된 검색/답변 전략
3. **inspireme 프론트엔드 챗봇 UI**: 기존 사이트에 채팅 위젯 통합

---

## 4. 데이터 소스 전략 (API → Document 변환)

### 4.1 변환 방식

inspireme 백엔드 API(`GET /api/quotes`, `GET /api/authors`)를 호출하여 데이터를 가져온 후 LangChain `Document` 객체로 변환한다. DB에 직접 접속하지 않으므로 스키마 변경에 영향받지 않는다. 명언은 1-2문장으로 짧기 때문에 **청킹 없이 1 명언 = 1 Document**로 처리한다.

#### Document 구조 — 명언

```python
Document(
    page_content="""
"{content_ko}"
"{content_en}"
— {author_name_ko} ({author_name_en})

주제: {topics}
태그: {tags}
저자 소개: {author_bio_ko}
""",
    metadata={
        "blog_id": "inspireme",
        "type": "quote",
        "quote_id": "uuid-xxx",
        "author": "알베르트 아인슈타인",
        "author_slug": "albert-einstein",
        "topics": ["인생", "지혜"],
        "tags": ["motivation", "wisdom"],
        "language": "ko",
        "url": "https://inspireme.advenoh.pe.kr/quotes/uuid-xxx",
    }
)
```

#### Document 구조 — 저자

```python
Document(
    page_content="""
{author_name_ko} ({author_name_en})
국적: {nationality}
출생: {birth_year}, 사망: {death_year}

소개 (한국어): {bio_ko}
소개 (English): {bio_en}
""",
    metadata={
        "blog_id": "inspireme",
        "type": "author",
        "author_id": "uuid-xxx",
        "author_slug": "albert-einstein",
        "nationality": "DE",
        "url": "https://inspireme.advenoh.pe.kr/authors/albert-einstein",
    }
)
```

### 4.2 다국어 처리

- `page_content`에 ko/en 번역을 **모두 포함**하여 어떤 언어로 질문해도 검색 가능
- 사용자 질문 언어에 따라 답변 언어를 결정하는 것은 LLM 프롬프트로 처리

### 4.3 인덱싱 파이프라인

```mermaid
flowchart LR
    A["POST /index/inspireme"] --> B["inspireme API 호출"]
    B --> C["GET /api/quotes (translations 포함)"]
    B --> D["GET /api/authors (ko + en)"]
    C --> E["Document 객체 변환"]
    D --> E
    E --> F["ChromaDB 'inspireme' collection에 저장"]
```

### 4.4 API 호출

```
GET /api/quotes?limit=1000&offset=0
  → 명언 목록 (페이지네이션, 결과 < limit이면 마지막 페이지)
  → 응답: [QuoteResponse] (content + translations + authorInfo + topics + tags)

GET /api/authors?lang=ko&limit=1000&offset=0
GET /api/authors?lang=en&limit=1000&offset=0
  → 저자 목록 (ko/en 각각 페이지네이션, total 기반 종료 판단 후 id 기준 병합)
  → 응답: {authors: [AuthorResponse], total: number}
```

**DB 직접 접속 대비 장점**:
- DB 스키마 변경 시 ai-chatbot 수정 불필요 (API 응답 구조만 유지되면 됨)
- DB 접속 정보 (host, port, user, password) 관리 불필요
- inspireme 백엔드가 데이터 접근의 단일 책임을 가짐

---

## 5. ai-chatbot 백엔드 변경사항

### 5.1 새로운 Document Loader

```
backend/app/rag/
├── document_loader.py          # 기존: Markdown 파일 로드
└── inspireme_loader.py         # 신규: inspireme API에서 명언/저자 로드
```

```python
# backend/app/rag/inspireme_loader.py

async def load_inspireme_documents(api_url: str) -> list[Document]:
    """inspireme API에서 명언/저자 데이터를 로드하여 Document 리스트로 반환"""
    # GET /api/quotes → 명언 Document 변환
    # GET /api/authors?lang=ko + lang=en → 저자 Document 변환 (ko/en 병합)
    return quotes_docs + author_docs
```

### 5.2 config.py 변경

```python
# blog_collections에 inspireme 추가
blog_collections = {
    "blog-v2": "IT 블로그",
    "investment": "투자 블로그",
    "inspireme": "명언",          # 신규
}

# inspireme API URL (환경변수)
inspireme_api_url: str = "http://localhost:8080"
```

### 5.3 인덱싱 엔드포인트 확장

```python
# backend/app/api/routes.py — /index/{blog_id}에 inspireme 분기 추가
# 참고: blog-v2/investment는 자동 인덱싱(#2)에서 git clone 방식으로 변경됨

@router.post("/index/{blog_id}")
async def reindex(blog_id: str, ...):
    manager.delete_collection(blog_id)

    if blog_id == "inspireme":
        # inspireme API에서 로드 (청킹 불필요 — 명언은 이미 짧음)
        documents = await load_inspireme_documents(settings.inspireme_api_url)
        indexed = manager.index_documents(blog_id, documents)
    elif blog_id in BLOG_REPOS:
        # git clone 방식으로 Markdown 파일 로드 + 청킹
        clone_dir = tempfile.mkdtemp(prefix=f"reindex-{blog_id}-")
        try:
            subprocess.run(["git", "clone", "--depth", "1", BLOG_REPOS[blog_id], clone_dir], ...)
            documents = load_blog_documents(f"{clone_dir}/contents/", blog_id)
            chunks = split_documents(documents, ...)
            indexed = manager.index_documents(blog_id, chunks)
        finally:
            shutil.rmtree(clone_dir, ignore_errors=True)
    else:
        raise HTTPException(status_code=400, detail=f"No repository for: {blog_id}")
```

### 5.4 inspireme 전용 프롬프트

```python
# backend/app/prompts/templates.py

INSPIREME_SYSTEM_PROMPT = """당신은 명언 추천 전문 AI 어시스턴트입니다.
사용자의 질문에 맞는 명언을 추천하고, 저자 정보를 안내합니다.

규칙:
- 검색된 명언을 인용할 때는 원문을 그대로 사용하세요
- 저자 이름과 출처를 반드시 함께 제공하세요
- 사용자의 감정이나 상황에 공감하며 적절한 명언을 추천하세요
- 검색 결과에 없는 명언을 지어내지 마세요
- 한국어로 답변하되, 영어 원문이 있으면 함께 제공하세요
"""
```

### 5.5 체인 선택 로직

```python
# backend/app/rag/chain.py — blog_id에 따라 프롬프트 분기
def create_rag_chain(retriever, blog_id: str):
    if blog_id == "inspireme":
        system_prompt = INSPIREME_SYSTEM_PROMPT
    else:
        system_prompt = DEFAULT_SYSTEM_PROMPT
    # 이하 기존 체인 생성 로직 동일
```

---

## 6. inspireme 프론트엔드 챗봇 UI 통합

### 6.1 통합 방식

inspireme 프론트엔드 우측 하단에 **플로팅 챗봇 버튼**을 추가한다. 클릭하면 챗봇 패널이 슬라이드업되어 나타난다.

### 6.2 동작 흐름

```mermaid
flowchart LR
    A["💬 플로팅 버튼 클릭"] --> B["챗봇 패널 열림"]
    B --> C["사용자 질문 입력"]
    C --> D["POST ai-chatbot.advenoh.pe.kr/chat"]
    D --> E["답변 + 출처 표시"]
    E --> F["출처 클릭 → 명언 상세 페이지 이동"]
```

### 6.3 컴포넌트 구조

```
inspireme.advenoh.pe.kr/frontend/
└── components/
    └── chatbot/
        ├── ChatbotButton.tsx       # 우측 하단 플로팅 버튼
        ├── ChatbotPanel.tsx        # 슬라이드업 챗봇 패널 (ChatWindow 역할)
        ├── ChatMessageList.tsx     # 메시지 목록
        └── ChatInput.tsx           # 입력 폼
```

### 6.4 API 연동

```typescript
// inspireme frontend에서 ai-chatbot 백엔드 직접 호출
const AI_CHATBOT_API = process.env.NEXT_PUBLIC_AI_CHATBOT_API_URL
  || "https://ai-chatbot.advenoh.pe.kr";

export async function sendChat(question: string, chatHistory: ChatMessage[]) {
  const response = await fetch(`${AI_CHATBOT_API}/chat`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      blog_id: "inspireme",
      question,
      chat_history: chatHistory,
    }),
  });
  return response.json();
}
```

### 6.5 UI 명세

| 요소 | 설명 |
|------|------|
| 플로팅 버튼 | 우측 하단 고정, `MessageCircle` 아이콘 (lucide-react) |
| 챗봇 패널 | 우측 하단 400×500px, 라운드 코너, 그림자 |
| 헤더 | "명언 AI 도우미" 타이틀 + 닫기 버튼 |
| 메시지 영역 | ScrollArea, 사용자(우측/파란)/AI(좌측/회색) |
| 출처 링크 | 명언 상세 페이지(`/quotes/{id}`)로 이동 |
| 입력 폼 | Input + Send 버튼, 엔터 키 제출 |
| 피드백 | 👍👎 버튼 (ai-chatbot의 기존 `/feedback` API 활용) |
| 추천 질문 | 초기 상태에서 예시 질문 표시 (선택 사항) |

### 6.6 추천 질문 예시

```
- "오늘 힘이 되는 명언 추천해줘"
- "아인슈타인의 명언이 있나요?"
- "인생에 대한 명언을 찾고 있어요"
- "동기부여가 되는 짧은 명언 알려줘"
```

---

## 7. 인덱싱 전략

### 7.1 트리거 방식

| 방식 | 설명 | 적용 |
|------|------|------|
| API 호출 | `POST /index/inspireme` + Bearer token | 수동 재인덱싱 |
| K8s CronJob | 기존 `ai-chatbot-reindex` CronJob의 `config.blogIds`에 `inspireme` 추가 | 주간 자동 (자동 인덱싱 #2에서 구축) |
| 명언 CRUD 시 | inspireme 백엔드에서 명언 생성/수정/삭제 후 ai-chatbot API 호출 | 실시간 반영 (향후) |

---

## 8. 환경변수 추가

### 8.1 ai-chatbot 백엔드 (`backend/.env`)

```bash
# inspireme API URL (인덱싱 시 사용)
INSPIREME_API_URL=http://inspireme-be-service.app.svc.cluster.local
```

### 8.2 inspireme 프론트엔드

```bash
# ai-chatbot API URL
NEXT_PUBLIC_AI_CHATBOT_API_URL=https://ai-chatbot.advenoh.pe.kr
```

---

## 9. 구현 순서 (마일스톤)

| 단계 | 작업 | 산출물 |
|------|------|--------|
| M1 | `inspireme_loader.py` — API → Document 변환 로직 + 테스트 | Document Loader |
| M2 | `/index/inspireme` 엔드포인트 확장 + config 추가 | 인덱싱 API |
| M3 | inspireme 전용 프롬프트 + 체인 분기 | RAG 체인 |
| M4 | inspireme 프론트엔드 챗봇 UI (플로팅 버튼 + 패널) | 챗봇 UI |
| M5 | 피드백 연동 + 추천 질문 + CronJob blogIds 추가 | 완성 |

---

## 10. 논의가 필요한 결정사항

### 10.1 임베딩 전략

명언은 1-2문장으로 매우 짧다. 현재 `text-embedding-3-small` 모델이 짧은 텍스트에서도 충분한 의미 검색 성능을 내는지 확인이 필요하다.

- **옵션 A**: 명언 텍스트만 임베딩 (현재 `page_content` 기준)
- **옵션 B**: 명언 + 저자 + 주제 + 태그를 합쳐서 임베딩 (컨텍스트 강화)
- **권장**: 옵션 B — 짧은 텍스트의 의미를 보강하기 위해 메타데이터를 `page_content`에 포함

### 10.2 검색 전략

- **Semantic Search만**: 현재 기본값, "힘이 되는 명언" 같은 의미 기반 질문에 적합
- **Hybrid Search (BM25 + Semantic)**: 저자 이름, 특정 키워드 검색에 유리
- **권장**: Hybrid Search — 명언 검색은 저자 이름/키워드 매칭이 빈번

### 10.3 인덱싱 단위

- **옵션 A**: 명언 Document + 저자 Document 분리 → 검색 결과 다양성 확보
- **옵션 B**: 명언 Document에 저자 정보 포함 → 단일 검색으로 충분한 컨텍스트
- **권장**: 옵션 A — "아인슈타인에 대해 알려줘" 같은 저자 중심 질문도 처리 가능

### 10.4 top_k 값

- 기존 blog-v2: `top_k=5` (긴 블로그 글 5개)
- inspireme: 명언이 짧으므로 더 많은 Document를 검색해도 컨텍스트 윈도우 여유
- **권장**: `top_k=10` 이상으로 설정하여 다양한 명언 추천

### 10.5 Cross-Origin 통신

inspireme 프론트엔드에서 ai-chatbot 백엔드를 직접 호출하면 CORS 설정이 필요하다.

- **옵션 A**: ai-chatbot 백엔드 CORS에 `inspireme.advenoh.pe.kr` 허용
- **옵션 B**: inspireme 백엔드에서 프록시 (Next.js rewrites)
- **권장**: 옵션 B — Next.js rewrites로 `/api/chatbot/*` → `ai-chatbot.advenoh.pe.kr/*` 프록시하면 CORS 이슈 없음

---

## 11. 테스트

### 11.1 Backend 테스트

**`tests/test_inspireme_loader.py`**:
- API 응답 → Document 변환 정확성 (명언 내용, 저자 정보, 메타데이터)
- 다국어 번역 포함 여부 (ko/en 병합)
- 빈 번역/authorInfo 없는 경우 fallback
- URL 생성 정확성

**`tests/test_api.py`** (확장):
- `POST /index/inspireme` → 인덱싱 성공 + Document 수 반환
- `POST /chat { blog_id: "inspireme" }` → 명언 검색 + 답변 생성
- 잘못된 blog_id → 400 에러

### 11.2 Frontend 테스트

- 플로팅 버튼 클릭 → 패널 열림/닫힘
- 질문 입력 → API 호출 → 답변 표시
- 출처 클릭 → 명언 상세 페이지 이동
- 피드백 버튼 동작
