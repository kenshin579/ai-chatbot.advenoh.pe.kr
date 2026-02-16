.PHONY: dev test index build lint clean

# Backend
dev:
	cd backend && uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8080

test:
	cd backend && uv run pytest -v

index:
	cd backend && uv run python scripts/index_documents.py --blog-id blog-v2 --contents-dir ../../blog-v2.advenoh.pe.kr/contents/

index-investment:
	cd backend && uv run python scripts/index_documents.py --blog-id investment --contents-dir ../../investment.advenoh.pe.kr/contents/

lint:
	cd backend && uv run ruff check .

build:
	cd backend && docker build -t kenshin579/rag-chatbot:latest .

# Setup
install:
	cd backend && uv sync

install-dev:
	cd backend && uv sync --extra dev

install-eval:
	cd backend && uv sync --extra eval

clean:
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .pytest_cache -exec rm -rf {} + 2>/dev/null || true
