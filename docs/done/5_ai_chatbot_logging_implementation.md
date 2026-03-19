# AI Chatbot Backend 구조화 로깅 구현

## 1. 의존성 추가

**파일**: `backend/pyproject.toml`

```toml
dependencies = [
    # 기존 의존성...
    "python-json-logger>=3.0",
]
```

설치: `cd backend && uv sync`

---

## 2. 로깅 설정 모듈 생성

**파일**: `backend/app/core/__init__.py` (빈 파일)
**파일**: `backend/app/core/logging.py`

```python
import logging
import sys
from pythonjsonlogger import jsonlogger


class _WarnLevelFormatter(jsonlogger.JsonFormatter):
    """WARNING → WARN 매핑으로 Go(slog)와 레벨명 통일"""

    def process_log_record(self, log_record: dict) -> dict:
        level = log_record.get("level", "")
        if level == "WARNING":
            log_record["level"] = "WARN"
        return super().process_log_record(log_record)


def init_logger(level: str = "INFO"):
    handler = logging.StreamHandler(sys.stdout)
    formatter = _WarnLevelFormatter(
        fmt="%(asctime)s %(levelname)s %(name)s %(message)s",
        rename_fields={
            "asctime": "time",
            "levelname": "level",
            "name": "source",
        },
        datefmt="%Y-%m-%dT%H:%M:%S.%f%z",
    )
    handler.setFormatter(formatter)

    root = logging.getLogger()
    root.handlers.clear()
    root.addHandler(handler)
    root.setLevel(getattr(logging, level.upper(), logging.INFO))

    # Uvicorn 로거 포맷 통일
    for name in ("uvicorn", "uvicorn.access", "uvicorn.error"):
        uv_logger = logging.getLogger(name)
        uv_logger.handlers.clear()
        uv_logger.addHandler(handler)
```

핵심 포인트:
- `python-json-logger`의 `JsonFormatter` 사용
- `WARNING` → `WARN` 매핑 (InspireMe Go slog와 호환)
- 필드명 통일: `time`, `level`, `source`
- Uvicorn 로거도 동일 JSON 포맷으로 통일

---

## 3. 요청/응답 로깅 미들웨어 생성

**파일**: `backend/app/middleware/__init__.py` (빈 파일)
**파일**: `backend/app/middleware/request_logging.py`

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
            logger.error("[SERVER ERROR] %s", msg, extra=log_data)
        elif response.status_code >= 400:
            logger.warning("[CLIENT ERROR] %s", msg, extra=log_data)
        else:
            logger.info("[RESPONSE] %s", msg, extra=log_data)

        return response
```

핵심 포인트:
- InspireMe와 동일한 필드: `remoteIp`, `method`, `uri`, `status`, `latency`, `userAgent`
- 상태 코드별 로그 레벨 자동 분류 (5xx=ERROR, 4xx=WARN, 나머지=INFO)
- f-string 대신 `%s` 포맷 사용 (lazy evaluation)

---

## 4. Settings에 로그 레벨 추가

**파일**: `backend/app/config.py`

```python
class Settings(BaseSettings):
    # 기존 설정...

    # Logging
    log_level: str = "INFO"
```

환경변수: `LOG_LEVEL=INFO` (기본값)

---

## 5. main.py에 로거 초기화 및 미들웨어 등록

**파일**: `backend/app/main.py`

```python
from app.core.logging import init_logger
from app.middleware.request_logging import RequestLoggingMiddleware

@asynccontextmanager
async def lifespan(app: FastAPI):
    init_logger(settings.log_level)  # 가장 먼저 초기화
    logger.info("Application starting")
    # 기존 MySQL 연결 코드...
    yield
    # 기존 종료 코드...

app = FastAPI(lifespan=lifespan)
app.add_middleware(RequestLoggingMiddleware)  # CORS 미들웨어 뒤에 추가
```

---

## 6. Silent Exception / print() 수정

### 6.1 `app/api/routes.py` — exception에 구조화 context 추가

```python
# 쿼리 로그 저장 실패
except Exception:
    logger.exception("쿼리 로그 저장 실패", extra={
        "blog_id": request.blog_id,
        "question": request.question[:100],
    })

# 피드백 저장 실패
except Exception:
    logger.exception("피드백 저장 실패", extra={
        "blog_id": request.blog_id,
    })

# LangSmith 피드백 전송 실패
except Exception:
    logger.exception("LangSmith 피드백 전송 실패", extra={
        "run_id": request.run_id,
    })
```

### 6.2 `app/rag/vector_store.py` — `except: pass` → logger.debug

```python
try:
    self.client.delete_collection(name=blog_id)
except Exception:
    logger.debug("Collection 삭제 스킵 (존재하지 않음)", extra={"blog_id": blog_id})
```

### 6.3 `app/rag/document_loader.py` — print() → logger.warning

```python
# Before: print(f"Warning: Failed to load {md_file}: {e}")
logger.warning("문서 로드 실패", extra={"file": str(md_file), "error": str(e)})
```

### 6.4 `scripts/index_documents.py`, `scripts/evaluate.py` — print() → logger.info

CLI 스크립트도 JSON 로그 포맷 통일. 스크립트 시작 시 `init_logger()` 호출 추가.

---

## 7. Uvicorn access log 중복 제거

**파일**: `backend/Dockerfile` 또는 실행 커맨드

```bash
uvicorn app.main:app --no-access-log
```

`Makefile`의 `run-be` 타겟에도 `--no-access-log` 플래그 추가.

---

## 8. InspireMe와의 로그 필드 호환성

| 필드 | InspireMe (Go) | AI Chatbot (Python) | 호환 |
|---|---|---|---|
| `time` | slog 기본 | JsonFormatter rename | ✅ |
| `level` | WARN | `_WarnLevelFormatter`로 WARN 매핑 | ✅ |
| `method` | String | String | ✅ |
| `uri` | String | String | ✅ |
| `status` | Integer | Integer | ✅ |
| `latency` | Integer (ms) | Integer (ms) | ✅ |
| `remoteIp` | String | String | ✅ |
| `userAgent` | String | String | ✅ |

---

## 9. 변경하지 않는 것

- RAG 체인 내부 상세 로깅 (LangSmith로 별도 관리)
- DB 쿼리 로깅 (SQLAlchemy 레벨) — 쿼리 수가 적어 우선순위 낮음
- 인덱싱 작업 진행률 로깅 — 별도 후속 작업
- `app/rag/document_loader.py`의 YAML 파싱 에러 (`metadata = {}`) — 의도된 동작
