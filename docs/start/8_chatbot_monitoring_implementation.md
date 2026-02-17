# RAG 챗봇 모니터링 - 구현 계획서

## 1. 프로젝트 구조 변경

### 1.1 Backend 신규/수정 파일

```
backend/
├── app/
│   ├── api/
│   │   ├── models.py          # FeedbackRequest, AdminStatsResponse 모델 추가
│   │   └── routes.py          # /feedback, /admin/stats 엔드포인트 추가
│   ├── db/                    # 신규 디렉토리
│   │   ├── __init__.py
│   │   ├── connection.py      # MySQL 연결 (SQLAlchemy AsyncSession)
│   │   ├── models.py          # ORM 모델 (QueryLog, Feedback)
│   │   └── repository.py      # DB 조회 함수 (통계, TOP 질문 등)
│   ├── config.py              # MySQL, ADMIN_TOKEN 설정 추가
│   └── main.py                # lifespan에 DB 초기화 추가
└── liquibase/                 # 신규 디렉토리 (DB 스키마 관리)
    ├── changelog.yaml         # 메인 changelog 설정
    ├── liquibase.properties   # 로컬 개발용 설정
    ├── lib/
    │   ├── mysql-connector-j-8.4.0.jar
    │   └── liquibase-natural-comparator.jar
    └── changes/
        └── 2026-02/
            ├── 1-create_query_logs.sql
            └── 2-create_feedbacks.sql
```

### 1.2 Frontend 신규/수정 파일

```
frontend/src/
├── app/
│   └── admin/
│       └── page.tsx              # 신규: Admin 대시보드 페이지
├── components/
│   ├── MessageList.tsx           # 수정: 👍👎 피드백 버튼 추가
│   └── admin/                    # 신규 디렉토리
│       ├── StatsCard.tsx         # 통계 카드
│       ├── QueryChart.tsx        # 일별 질문 수 차트
│       ├── TopQuestions.tsx       # 인기 질문 목록
│       └── CollectionInfo.tsx    # 인덱싱 현황
└── lib/
    └── api.ts                    # sendFeedback, getAdminStats 함수 추가
```

### 1.3 Charts 수정 파일

```
charts/charts/
├── mysql/values.yaml                          # ai_chatbot DB/사용자 추가
├── ai-chatbot-be/
│   ├── values.yaml                            # MySQL, ADMIN_TOKEN, liquibase 설정 추가
│   ├── templates/configmap.yaml               # MySQL 환경변수 추가
│   ├── templates/secret.yaml                  # DB 비밀번호, ADMIN_TOKEN 추가 (PreSync wave 0)
│   └── templates/presync-liquibase.yaml       # 신규: Liquibase PreSync Job (wave 1)
└── gateway/values.yaml                        # /feedback, /admin 라우트 추가
```

---

## 2. Backend 구현

### 2.1 의존성 추가 (`pyproject.toml`)

```toml
[project]
dependencies = [
    # 기존 의존성...
    "sqlalchemy[asyncio]>=2.0",
    "aiomysql>=0.2.0",
]
```

### 2.2 설정 추가 (`app/config.py`)

```python
class Settings(BaseSettings):
    # 기존 설정...

    # MySQL
    mysql_host: str = "localhost"
    mysql_port: int = 3306
    mysql_database: str = "ai_chatbot"
    mysql_user: str = "ai_chatbot"
    mysql_password: str = ""

    # Admin
    admin_token: str = ""

    @property
    def database_url(self) -> str:
        return (
            f"mysql+aiomysql://{self.mysql_user}:{self.mysql_password}"
            f"@{self.mysql_host}:{self.mysql_port}/{self.mysql_database}"
        )
```

### 2.3 DB 연결 (`app/db/connection.py`)

```python
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

engine = None
async_session_factory = None

async def init_db(database_url: str):
    global engine, async_session_factory
    engine = create_async_engine(database_url, pool_pre_ping=True)
    async_session_factory = async_sessionmaker(engine, expire_on_commit=False)

async def get_session() -> AsyncSession:
    async with async_session_factory() as session:
        yield session

async def close_db():
    if engine:
        await engine.dispose()
```

### 2.4 ORM 모델 (`app/db/models.py`)

```python
from sqlalchemy import BigInteger, String, Text, Integer, Boolean, JSON, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from datetime import datetime

class Base(DeclarativeBase):
    pass

class QueryLog(Base):
    __tablename__ = "query_logs"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    message_id: Mapped[str] = mapped_column(String(255), nullable=False)
    blog_id: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    question: Mapped[str] = mapped_column(Text, nullable=False)
    answer: Mapped[str] = mapped_column(Text, nullable=False)
    sources: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    response_time_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    has_results: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now(), index=True)

class Feedback(Base):
    __tablename__ = "feedbacks"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    message_id: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    blog_id: Mapped[str] = mapped_column(String(100), nullable=False)
    question: Mapped[str] = mapped_column(Text, nullable=False)
    rating: Mapped[str] = mapped_column(String(10), nullable=False)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now(), index=True)
```

### 2.5 Repository (`app/db/repository.py`)

```python
from sqlalchemy import select, func, case
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.models import QueryLog, Feedback

class QueryLogRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def save_query_log(self, **kwargs):
        log = QueryLog(**kwargs)
        self.session.add(log)
        await self.session.commit()

    async def save_feedback(self, **kwargs):
        fb = Feedback(**kwargs)
        self.session.add(fb)
        await self.session.commit()

    async def get_daily_counts(self, days: int = 30) -> list[dict]:
        """일별 질문 수 조회"""
        ...

    async def get_top_questions(self, limit: int = 10) -> list[dict]:
        """가장 많이 물어본 질문 TOP N"""
        ...

    async def get_feedback_ratio(self) -> dict:
        """👍👎 비율 계산"""
        ...

    async def get_avg_response_time(self) -> float:
        """평균 응답 시간 (ms)"""
        ...

    async def get_search_failure_rate(self) -> float:
        """검색 실패율 (has_results=False 비율)"""
        ...
```

### 2.6 API 엔드포인트 수정 (`app/api/routes.py`)

#### `/chat` 수정 - 쿼리 로깅 추가

```python
@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest, session: AsyncSession = Depends(get_session)):
    start_time = time.time()

    # 기존 RAG 처리 로직...
    result = chain.invoke({"input": request.question, "chat_history": messages})

    response_time_ms = int((time.time() - start_time) * 1000)

    # 쿼리 로그 저장
    repo = QueryLogRepository(session)
    await repo.save_query_log(
        message_id=run_id,
        blog_id=request.blog_id,
        question=request.question,
        answer=result["answer"],
        sources=[s.dict() for s in sources],
        response_time_ms=response_time_ms,
        has_results=len(sources) > 0,
    )

    return ChatResponse(answer=result["answer"], sources=sources, message_id=run_id)
```

#### `/feedback` 신규

```python
@router.post("/feedback")
async def feedback(request: FeedbackRequest, session: AsyncSession = Depends(get_session)):
    repo = QueryLogRepository(session)
    await repo.save_feedback(
        message_id=request.message_id,
        blog_id=request.blog_id,
        question=request.question,
        rating=request.rating,
    )
    # LangSmith Feedback API 연동
    if settings.langchain_tracing_v2:
        client = Client()
        client.create_feedback(
            run_id=request.message_id,
            key="user-score",
            score=1.0 if request.rating == "up" else 0.0,
        )
    return {"status": "ok"}
```

#### `/admin/stats` 신규

```python
def verify_admin_token(token: str = Header(alias="X-Admin-Token")):
    if token != settings.admin_token:
        raise HTTPException(status_code=401, detail="Invalid admin token")

@router.get("/admin/stats")
async def get_stats(
    _: str = Depends(verify_admin_token),
    session: AsyncSession = Depends(get_session),
):
    repo = QueryLogRepository(session)
    return {
        "daily_queries": await repo.get_daily_counts(),
        "top_questions": await repo.get_top_questions(limit=10),
        "feedback_score": await repo.get_feedback_ratio(),
        "avg_response_time": await repo.get_avg_response_time(),
        "search_failure_rate": await repo.get_search_failure_rate(),
        "collections": vector_store_manager.get_collection_stats(),
    }
```

### 2.7 ChatResponse에 message_id 추가 (`app/api/models.py`)

```python
class ChatResponse(BaseModel):
    answer: str
    sources: list[Source]
    message_id: str  # 추가: LangSmith run_id

class FeedbackRequest(BaseModel):
    message_id: str
    blog_id: str
    question: str
    rating: Literal["up", "down"]
```

### 2.8 앱 lifespan 수정 (`app/main.py`)

```python
from contextlib import asynccontextmanager
from app.db.connection import init_db, close_db

@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db(settings.database_url)
    yield
    await close_db()

app = FastAPI(title="RAG Chatbot API", version="0.2.0", lifespan=lifespan)
```

---

## 3. Frontend 구현

### 3.1 의존성 추가 (`package.json`)

```json
{
  "dependencies": {
    "recharts": "^2.15.0"
  }
}
```

### 3.2 API 클라이언트 확장 (`src/lib/api.ts`)

```typescript
// ChatResponse에 message_id 추가
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

export async function sendFeedback(request: FeedbackRequest): Promise<void> {
  await fetch(`${API_BASE_URL}/feedback`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(request),
  });
}

export interface AdminStats {
  daily_queries: { date: string; count: number }[];
  top_questions: { question: string; count: number }[];
  feedback_score: { up: number; down: number; ratio: number };
  avg_response_time: number;
  search_failure_rate: number;
  collections: { name: string; count: number }[];
}

export async function getAdminStats(token: string): Promise<AdminStats> {
  const res = await fetch(`${API_BASE_URL}/admin/stats`, {
    headers: { "X-Admin-Token": token },
  });
  return res.json();
}
```

### 3.3 피드백 버튼 (`MessageList.tsx` 수정)

AI 메시지 하단에 👍👎 버튼 추가. 클릭 시 `sendFeedback()` 호출. 클릭 후 버튼 비활성화 (중복 방지).

### 3.4 Admin 대시보드 (`src/app/admin/page.tsx`)

- 토큰 입력 → 통계 API 호출
- StatsCard: 총 질문 수, 피드백 비율, 평균 응답 시간, 검색 실패율
- QueryChart: recharts `LineChart`로 일별 질문 수 추이
- TopQuestions: 테이블 형태로 인기 질문 10개
- CollectionInfo: Collection별 문서 수

---

## 4. Charts 변경

### 4.1 MySQL DB/사용자 추가 (`charts/mysql/values.yaml`)

`initdbScripts.init-permissions.sql`에 추가:

```sql
CREATE DATABASE IF NOT EXISTS `ai_chatbot`
CHARACTER SET utf8mb4
COLLATE utf8mb4_0900_ai_ci;
CREATE USER IF NOT EXISTS 'ai_chatbot'@'%'
IDENTIFIED WITH mysql_native_password
BY '<비밀번호>';
GRANT ALL PRIVILEGES ON `ai_chatbot`.* TO 'ai_chatbot'@'%';
```

### 4.2 ai-chatbot-be 설정 추가 (`charts/ai-chatbot-be/values.yaml`)

```yaml
config:
  # 기존 설정...
  mysqlHost: "mysql-headless.app.svc.cluster.local"
  mysqlPort: "3306"
  mysqlDatabase: "ai_chatbot"

secrets:
  # 기존 설정...
  mysql:
    user: "ai_chatbot"
    password: "<비밀번호>"
  admin:
    token: "<admin-token>"

liquibase:
  enabled: true
  email:
    enabled: false
    recipients: "kenshin579@gmail.com"
    from:
      name: "AI-Chatbot Notifier"
      address: "ai-chatbot@finance-cluster.local"
    smtp:
      host: "postfix.app.svc.cluster.local"
      port: 25
```

### 4.3 ConfigMap 템플릿 수정 (`charts/ai-chatbot-be/templates/configmap.yaml`)

MySQL 환경변수 추가:
- `MYSQL_HOST`, `MYSQL_PORT`, `MYSQL_DATABASE`

### 4.4 Secret 템플릿 수정 (`charts/ai-chatbot-be/templates/secret.yaml`)

- PreSync 어노테이션 추가 (wave 0, Liquibase Job보다 먼저 생성)
- `AI_CHATBOT_MYSQL_HOST`, `AI_CHATBOT_MYSQL_PORT`, `AI_CHATBOT_MYSQL_DATABASE`
- `AI_CHATBOT_MYSQL_USERNAME`, `AI_CHATBOT_MYSQL_PASSWORD`
- `ADMIN_TOKEN`

```yaml
annotations:
  argocd.argoproj.io/hook: PreSync
  argocd.argoproj.io/sync-wave: "0"
```

### 4.5 PreSync Liquibase Job 생성 (`charts/ai-chatbot-be/templates/presync-liquibase.yaml`)

`inspireme-be/templates/presync-liquibase.yaml` 패턴을 그대로 따른다.

```yaml
# 핵심 구조 (inspireme-be 패턴 동일)
annotations:
  argocd.argoproj.io/hook: PreSync
  argocd.argoproj.io/hook-delete-policy: BeforeHookCreation
  argocd.argoproj.io/sync-wave: "1"

initContainers:
  # 1. copy-changelog: ai-chatbot-be 이미지에서 /liquibase/ 파일 복사
  - name: copy-changelog
    image: {{ .Values.image.name_tag }}
    # /liquibase/changelog/, /liquibase/lib/ → emptyDir volumes

  # 2. run-liquibase: Liquibase 4.30.0으로 migration 실행
  - name: run-liquibase
    image: docker.io/liquibase/liquibase:4.30.0
    env:
      - name: MYSQL_HOST/PORT/DATABASE/USERNAME/PASSWORD
        valueFrom: secretKeyRef (ai-chatbot-be-secret)
    command: liquibase status && liquibase update
```

### 4.6 Backend Dockerfile 수정

Liquibase 파일을 Docker 이미지에 포함:

```dockerfile
# 기존 빌드 단계 이후
COPY liquibase/changelog.yaml /liquibase/changelog/changelog.yaml
COPY liquibase/changes/ /liquibase/changelog/changes/
COPY liquibase/lib/ /liquibase/lib/
```

### 4.7 Gateway 라우트 추가 (`charts/gateway/values.yaml`)

`ai-chatbot.advenoh.pe.kr` 도메인에 추가 라우트:
- `/feedback` → `ai-chatbot-be-service:80`
- `/admin` → `ai-chatbot-be-service:80` (stats API)
- `/admin` → `ai-chatbot-fe-service:80` (대시보드 UI, 프론트엔드)

---

## 5. 테스트

### 5.1 Backend 단위 테스트

- `test_feedback_api.py`: POST /feedback 정상 저장 확인
- `test_admin_api.py`: GET /admin/stats 토큰 인증 및 응답 형태 확인
- `test_query_log.py`: /chat 호출 시 query_logs 테이블 기록 확인

### 5.2 E2E 테스트 (MCP Playwright)

- 채팅 후 👍👎 버튼 표시 확인
- 피드백 버튼 클릭 → API 호출 확인
- `/admin` 페이지 접근 → 통계 데이터 렌더링 확인
- 차트/카드 컴포넌트 정상 표시 확인
