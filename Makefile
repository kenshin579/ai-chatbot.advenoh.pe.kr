.PHONY: help run-fe run-be run-all test index lint build install clean tag docker-push

# ========================================
# 도움말
# ========================================

help:
	@echo "AI Chatbot 개발 명령어"
	@echo ""
	@echo "개발 서버:"
	@echo "  run-fe        Frontend 실행 (Next.js, 포트 3000)"
	@echo "  run-be        Backend 실행 (FastAPI, 포트 8080)"
	@echo "  run-all       Frontend + Backend 동시 실행"
	@echo ""
	@echo "개발 도구:"
	@echo "  test           테스트 실행"
	@echo "  lint           린트 검사"
	@echo "  index          blog-v2 문서 인덱싱"
	@echo "  index-invest   투자 블로그 문서 인덱싱"
	@echo "  install        의존성 설치"
	@echo ""
	@echo "릴리스:"
	@echo "  make tag patch|minor|major   버전 태그 생성"
	@echo "  make docker-push fe|be|all   Docker 이미지 푸시"

# ========================================
# 개발 서버 실행
# ========================================

run-fe:
	@cd frontend && npm run dev

run-be:
	@cd backend && uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8080

run-all:
	@cd backend && uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8080 & cd frontend && npm run dev

# ========================================
# 개발 도구
# ========================================

test:
	@cd backend && uv run pytest -v

lint:
	@cd backend && uv run ruff check .

index:
	@cd backend && uv run python scripts/index_documents.py --blog-id blog-v2 --contents-dir ../../blog-v2.advenoh.pe.kr/contents/

index-invest:
	@cd backend && uv run python scripts/index_documents.py --blog-id investment --contents-dir ../../investment.advenoh.pe.kr/contents/

build:
	@cd backend && docker build -t kenshin579/ai-chatbot-be:latest .

install:
	@cd backend && uv sync

install-dev:
	@cd backend && uv sync --extra dev

install-eval:
	@cd backend && uv sync --extra eval

clean:
	@find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	@find . -type d -name .pytest_cache -exec rm -rf {} + 2>/dev/null || true

# ========================================
# 릴리스 및 배포
# ========================================

# 태그 및 릴리스 (인자: patch, minor, major)
# 사용법: make tag patch / make tag minor / make tag major
tag:
	@./scripts/release.sh $(filter-out $@,$(MAKECMDGOALS))

# Docker 빌드 및 푸시 (인자: fe, be, all)
# 사용법: make docker-push fe / make docker-push be / make docker-push all
docker-push:
	@./scripts/docker-push.sh $(filter-out $@,$(MAKECMDGOALS))

# 인자를 타겟으로 인식하지 않도록 처리
%:
	@:
