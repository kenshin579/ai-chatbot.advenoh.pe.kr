# AI Chatbot Backend 구조화 로깅 도입 PRD

## 1. 배경

AI Chatbot 백엔드(FastAPI + Python)는 로깅이 거의 없는 상태로, 운영 환경에서 RAG 파이프라인 문제 추적과 사용량 모니터링이 불가능하다.

### 현재 상태 vs InspireMe 기준

| 항목 | InspireMe 기준 (Go) | AI Chatbot (현재) |
|---|---|---|
| 로그 포맷 | JSON (slog) | 텍스트 (Python logging 기본) |
| HTTP 요청 로깅 | 커스텀 미들웨어 (method, uri, status, latency 등) | ❌ 없음 (Uvicorn 기본 access log만) |
| 에러 로깅 | 5xx/4xx 자동 분류 | exception 3건만 (catch 블록에서) |
| DB 쿼리 로깅 | GORM 커스텀 로거 | ❌ 없음 |
| 로그 레벨 설정 | config.yaml에서 설정 | ❌ 없음 |
| 전체 로그 구문 수 | 다수 | **8건** (대부분 exception 핸들러) |
| silent exception | 없음 | 다수 (`except: pass`, `print()`) |

### 문제점

1. **요청 추적 불가**: HTTP 요청/응답이 로그에 기록되지 않아 OpenSearch에서 API 트래픽 분석 불가
2. **RAG 파이프라인 불투명**: 체인 실행 시간, 검색 결과 수, 토큰 사용량 등이 로그에 없음
3. **사일런트 에러**: `except: pass` 패턴으로 에러가 삼켜지는 곳이 다수
4. **로그 포맷 불일치**: `print()`, `logging`, Uvicorn 기본 로그가 혼재 → Fluent-bit 파싱 어려움
5. **대시보드 구축 불가**: 3_dashboard_prd.md의 AI Chatbot 대시보드에 데이터 없음

---

## 2. 목표

InspireMe의 구조화 로깅 원칙(JSON, 레벨 분류, 요청/응답 필드)을 Python/FastAPI에 맞게 적용한다.

### 완료 조건

- [ ] JSON 구조화 로깅 설정 (python-json-logger 또는 structlog)
- [ ] FastAPI 요청/응답 로깅 미들웨어 추가
- [ ] 로그 레벨 설정 가능 (환경변수)
- [ ] silent exception 제거 (로깅으로 교체)
- [ ] OpenSearch `ai-chatbot-*` 인덱스에 구조화된 JSON 로그가 수집되는 것 확인

---

## 3. 변경 범위

### 3.1 신규 파일

#### `app/core/logging.py` — 로깅 설정 모듈

```python
import logging
import sys
from pythonjsonlogger import jsonlogger

def init_logger(level: str = "INFO"):
    """JSON 구조화 로거 초기화"""
    handler = logging.StreamHandler(sys.stdout)

    formatter = jsonlogger.JsonFormatter(
        fmt="%(asctime)s %(levelname)s %(name)s %(message)s",
        rename_fields={
            "asctime": "time",
            "levelname": "level",
            "name": "source",
        },
        datefmt="%Y-%m-%dT%H:%M:%S.%f%z",
    )
    handler.setFormatter(formatter)

    root_logger = logging.getLogger()
    root_logger.handlers.clear()
    root_logger.addHandler(handler)
    root_logger.setLevel(getattr(logging, level.upper(), logging.INFO))

    # Uvicorn 로거도 동일 포맷으로 통일
    for name in ("uvicorn", "uvicorn.access", "uvicorn.error"):
        uv_logger = logging.getLogger(name)
        uv_logger.handlers.clear()
        uv_logger.addHandler(handler)
```

#### `app/middleware/request_logging.py` — 요청/응답 로깅 미들웨어

```python
import logging
import time
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

logger = logging.getLogger(__name__)

class RequestLoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        start = time.time()
        response = await call_next(request)
        latency_ms = int((time.time() - start) * 1000)

        log_data = {
            "remoteIp": request.client.host if request.client else "",
            "host": request.headers.get("host", ""),
            "method": request.method,
            "uri": str(request.url.path),
            "status": response.status_code,
            "latency": latency_ms,
            "latency_human": f"{latency_ms}ms",
            "userAgent": request.headers.get("user-agent", ""),
        }

        msg = f"{request.method} {request.url.path}"

        if response.status_code >= 500:
            logger.error(f"[SERVER ERROR] {msg}", extra=log_data)
        elif response.status_code >= 400:
            logger.warning(f"[CLIENT ERROR] {msg}", extra=log_data)
        else:
            logger.info(f"[RESPONSE] {msg}", extra=log_data)

        return response
```

### 3.2 수정 파일

#### `app/config.py`

Settings에 로깅 설정 추가:

```python
class Settings(BaseSettings):
    # 기존 설정 유지...

    # Logging (추가)
    log_level: str = "INFO"
```

환경변수: `LOG_LEVEL=INFO`

#### `app/main.py`

로거 초기화 및 미들웨어 등록:

```python
from app.core.logging import init_logger
from app.middleware.request_logging import RequestLoggingMiddleware

@asynccontextmanager
async def lifespan(app: FastAPI):
    # 로거 초기화 (가장 먼저)
    init_logger(settings.log_level)
    logger.info("Application starting")

    # 기존 MySQL 연결 코드...
    yield
    # 기존 종료 코드...

app = FastAPI(lifespan=lifespan)
app.add_middleware(RequestLoggingMiddleware)
```

#### `app/api/routes.py` — silent exception 수정

**Before**:
```python
except Exception:
    logger.exception("쿼리 로그 저장 실패")
```

**After** (구조화된 context 추가):
```python
except Exception:
    logger.exception("쿼리 로그 저장 실패", extra={
        "blog_id": request.blog_id,
        "question": request.question[:100],
    })
```

#### `app/rag/vector_store.py` — silent exception 제거

**Before**:
```python
try:
    self.client.delete_collection(name=blog_id)
except Exception:
    pass  # Collection이 없으면 무시
```

**After**:
```python
try:
    self.client.delete_collection(name=blog_id)
except Exception:
    logger.debug("Collection 삭제 스킵 (존재하지 않음)", extra={"blog_id": blog_id})
```

#### `app/rag/document_loader.py` — print → logger

**Before**:
```python
print(f"Warning: Failed to load {md_file}: {e}")
```

**After**:
```python
logger.warning("문서 로드 실패", extra={"file": str(md_file), "error": str(e)})
```

#### `scripts/index_documents.py`, `scripts/evaluate.py`

`print()` → `logger.info()` 로 교체 (CLI 스크립트도 JSON 출력 통일)

### 3.3 의존성 추가

`pyproject.toml`에 추가:

```toml
dependencies = [
    # 기존 의존성...
    "python-json-logger>=3.0",
]
```

---

## 4. 변경하지 않는 것

- RAG 체인 내부의 상세 로깅 (LangChain 트레이싱은 LangSmith로 별도 관리)
- DB 쿼리 로깅 (SQLAlchemy 레벨) — 현재 쿼리 수가 적어 우선순위 낮음
- 인덱싱 작업의 진행률 로깅 — 별도 후속 작업

---

## 5. 기대 로그 출력

### HTTP 요청 로그 (성공)

```json
{
  "time": "2026-03-18T10:30:00.123000+0900",
  "level": "INFO",
  "source": "app.middleware.request_logging",
  "message": "[RESPONSE] POST /chat",
  "remoteIp": "192.168.1.10",
  "host": "ai-chatbot.advenoh.pe.kr",
  "method": "POST",
  "uri": "/chat",
  "status": 200,
  "latency": 3450,
  "latency_human": "3450ms",
  "userAgent": "Mozilla/5.0..."
}
```

### HTTP 요청 로그 (에러)

```json
{
  "time": "2026-03-18T10:30:01.456000+0900",
  "level": "ERROR",
  "source": "app.middleware.request_logging",
  "message": "[SERVER ERROR] POST /chat",
  "status": 500,
  "latency": 5012,
  "error": "ChromaDB connection refused"
}
```

### 예외 로그

```json
{
  "time": "2026-03-18T10:30:02.789000+0900",
  "level": "ERROR",
  "source": "app.api.routes",
  "message": "쿼리 로그 저장 실패",
  "blog_id": "frank-blog",
  "question": "OpenSearch 대시보드 구성 방법은?",
  "exc_info": "Traceback (most recent call last)..."
}
```

---

## 6. InspireMe와의 로그 필드 호환성

OpenSearch 대시보드에서 서비스 간 통합 조회를 위해 핵심 필드명을 맞춘다.

| 필드 | InspireMe (Go) | AI Chatbot (Python) | 호환 |
|---|---|---|---|
| `time` | slog 기본 | JsonFormatter rename | ✅ |
| `level` | INFO/WARN/ERROR | INFO/WARNING/ERROR | ⚠️ 주의 |
| `method` | String | String | ✅ |
| `uri` | String | String | ✅ |
| `status` | Integer | Integer | ✅ |
| `latency` | Integer (ms) | Integer (ms) | ✅ |
| `remoteIp` | String | String | ✅ |
| `userAgent` | String | String | ✅ |
| `error` | String | String | ✅ |

> ⚠️ **Python의 WARNING vs Go의 WARN**: Python logging은 `WARNING`을 사용하고 Go slog는 `WARN`을 사용한다.
> JsonFormatter에서 `WARNING` → `WARN`으로 매핑하거나, OpenSearch 쿼리에서 양쪽 모두 처리해야 한다.

---

## 7. 검증 방법

1. 로컬에서 `make run-be` 후 `/chat` 호출 → stdout에 JSON 로그 출력 확인
2. `level`, `status`, `latency` 필드가 올바른 타입인지 확인
3. Uvicorn 기본 access log가 JSON으로 통일되었는지 확인
4. Kind 클러스터 배포 후 OpenSearch Dashboards의 `ai-chatbot-*` 인덱스에서:
   - InspireMe와 동일한 필드명으로 검색 가능한지 확인
   - 통합 대시보드에서 서비스 간 비교 쿼리 동작 확인

---

## 8. 논의사항

### 8.1 로깅 라이브러리 선택

| 옵션 | 장점 | 단점 |
|---|---|---|
| **python-json-logger** | 가볍고 단순, stdlib logging 호환 | 기능 제한적 |
| **structlog** | 풍부한 기능, 프로세서 파이프라인 | 학습 비용, 의존성 큼 |
| **loguru** | 간편한 API, 자동 포맷팅 | stdlib logging과 호환성 이슈 |

- **권장**: `python-json-logger` — 가장 가볍고 기존 코드 변경 최소화

### 8.2 WARNING vs WARN 레벨 통일

- Python: `WARNING`, Go: `WARN`
- OpenSearch 대시보드에서 서비스 간 통합 쿼리 시 불일치 발생
- **옵션 A**: Python 측에서 `WARNING` → `WARN`으로 매핑 (JsonFormatter 커스텀)
- **옵션 B**: OpenSearch 쿼리에서 `level: WARN OR level: WARNING`으로 처리
- **권장**: 옵션 A (소스에서 통일하는 것이 대시보드 쿼리가 단순해짐)

### 8.3 Uvicorn access log 중복

- RequestLoggingMiddleware가 요청을 로깅하면 Uvicorn 기본 access log와 중복될 수 있음
- **권장**: Uvicorn 시작 시 `--access-log` 비활성화하고 미들웨어 로그만 사용
- Dockerfile 또는 실행 커맨드에서: `uvicorn app.main:app --no-access-log`

### 8.4 RAG 체인 실행 로깅 범위

- 현재 LangChain 트레이싱은 LangSmith(`LANGCHAIN_TRACING_V2`)로 설정 가능하나 비활성 상태
- RAG 파이프라인 내부 로깅(검색 문서 수, 리랭킹 결과, 토큰 수)은 이번 범위에 포함할지?
- **권장**: 이번에는 HTTP 레벨 로깅만 적용, RAG 내부는 LangSmith 활성화로 별도 추적

### 8.5 query_logs 테이블과의 관계

- 현재 `/chat` 요청의 상세 정보(question, answer, tokens, duration)는 MySQL `query_logs` 테이블에 저장됨
- 이 데이터를 로그로도 출력할지, DB 저장만 유지할지?
- **권장**: DB 저장 유지 + 로그에는 요약 정보만 (blog_id, duration_ms, has_results 정도)
