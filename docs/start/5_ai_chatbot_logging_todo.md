# AI Chatbot Backend 구조화 로깅 TODO

## Phase 1: 기반 설정

- [ ] `pyproject.toml`에 `python-json-logger>=3.0` 의존성 추가
- [ ] `uv sync`로 의존성 설치
- [ ] `app/core/__init__.py` 생성 (빈 파일)
- [ ] `app/core/logging.py` 생성 — JSON 로거 초기화 + WARNING→WARN 매핑
- [ ] `app/config.py`에 `log_level: str = "INFO"` 설정 추가

## Phase 2: 미들웨어

- [ ] `app/middleware/__init__.py` 생성 (빈 파일)
- [ ] `app/middleware/request_logging.py` 생성 — HTTP 요청/응답 로깅 미들웨어
- [ ] `app/main.py`에 `init_logger(settings.log_level)` 호출 추가 (lifespan 시작부분)
- [ ] `app/main.py`에 `RequestLoggingMiddleware` 등록

## Phase 3: 기존 코드 로깅 개선

- [ ] `app/api/routes.py` — 3개 exception handler에 구조화 context(extra) 추가
  - [ ] 쿼리 로그 저장 실패: `blog_id`, `question` 추가
  - [ ] 피드백 저장 실패: `blog_id` 추가
  - [ ] LangSmith 피드백 전송 실패: `run_id` 추가
- [ ] `app/rag/vector_store.py` — `except: pass` → `logger.debug()` 교체
- [ ] `app/rag/document_loader.py` — `print()` → `logger.warning()` 교체

## Phase 4: 스크립트 로깅 통일

- [ ] `scripts/index_documents.py` — `print()` → `logger.info()` 교체 + `init_logger()` 호출 추가
- [ ] `scripts/evaluate.py` — `print()` → `logger.info()` 교체 + `init_logger()` 호출 추가

## Phase 5: Uvicorn 설정

- [ ] Uvicorn 실행 시 `--no-access-log` 플래그 추가 (미들웨어 로그와 중복 제거)
  - [ ] `Makefile`의 `run-be` 타겟 수정
  - [ ] `Dockerfile`의 CMD 수정

## Phase 6: 검증

- [ ] 로컬 `make run-be` 후 `/health` 호출 → stdout에 JSON 로그 출력 확인
- [ ] `/chat` 호출 → 요청/응답 로그에 `method`, `uri`, `status`, `latency` 필드 확인
- [ ] 에러 케이스 → 5xx/4xx 로그 레벨 분류 확인
- [ ] Uvicorn 기본 access log가 JSON으로 통일되었는지 확인
- [ ] `LOG_LEVEL=DEBUG` 환경변수로 레벨 변경 동작 확인
- [ ] `make test` — 기존 테스트 통과 확인
- [ ] MCP Playwright로 웹 UI에서 채팅 후 백엔드 로그 JSON 포맷 확인
