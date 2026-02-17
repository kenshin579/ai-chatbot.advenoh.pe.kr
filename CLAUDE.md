# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

RAG(Retrieval-Augmented Generation) 기반 블로그 Q&A 챗봇. 블로그 콘텐츠를 ChromaDB에 인덱싱하고 사용자 질문에 관련 문서를 검색하여 답변을 생성한다. Frontend(Next.js)와 Backend(FastAPI)로 구성된 모노레포.

## Common Commands

```bash
# 개발 서버
make run-fe          # Frontend (Next.js, 포트 3000)
make run-be          # Backend (FastAPI, 포트 8080)
make run-all         # Frontend + Backend 동시 실행

# 의존성 설치
make install         # Backend (uv sync)
make install-dev     # Backend dev 의존성 포함
cd frontend && npm install  # Frontend

# 테스트 & 린트
make test            # Backend pytest (cd backend && uv run pytest -v)
make lint            # Backend ruff (cd backend && uv run ruff check .)

# 단일 테스트 실행
cd backend && uv run pytest tests/test_api.py -v
cd backend && uv run pytest tests/test_api.py::test_health_check -v

# 문서 인덱싱
make index           # blog-v2 인덱싱
make index-invest    # 투자 블로그 인덱싱

# 릴리스 & 배포
make tag patch|minor|major    # 버전 태그 생성 (GitHub Actions 트리거)
make docker-push fe|be|all    # Docker 이미지 빌드 & 푸시
```

## Architecture

### Frontend (`frontend/`)
- **Next.js 16** App Router, React 19, TypeScript strict mode
- **UI**: shadcn/ui (Radix UI) + Tailwind CSS 4
- `src/app/page.tsx` → `ChatWindow` 컴포넌트가 메인 채팅 UI
- `src/lib/api.ts` → Backend API 호출 (`sendChat`)
- `next.config.ts`: `output: "standalone"` (Docker 최적화)
- Path alias: `@/*` → `./src/*`

### Backend (`backend/`)
- **FastAPI** + **LangChain** + **ChromaDB** + **OpenAI**
- Package manager: **uv** (Astral), Python 3.12+

#### API Endpoints (`app/api/routes.py`)
- `POST /chat` — 질문 + blog_id + chat_history → 답변 + 출처
- `POST /index/{blog_id}` — 문서 재인덱싱 (Bearer token 인증)
- `GET /health` — 헬스체크

#### RAG Pipeline (`app/rag/`)
1. `document_loader.py` — Markdown 파일 로드, YAML frontmatter 파싱
2. `chunker.py` — RecursiveCharacterTextSplitter (Markdown 구분자 기반)
3. `embedder.py` — OpenAI text-embedding-3-small
4. `vector_store.py` — ChromaDB HttpClient (blog_id별 collection 분리)
5. `retriever.py` — Semantic 검색 + BM25 하이브리드 (선택적)
6. `chain.py` — LangChain RAG chain (대화 이력 기반 질문 재구성)

#### Multi-Blog Support
- `config.py`의 `blog_collections` dict로 blog_id → ChromaDB collection 매핑
- 현재: `blog-v2` (IT 블로그), `investment` (투자 블로그)

### Configuration (`backend/app/config.py`)
- Pydantic Settings + `.env` 파일
- `@lru_cache`로 설정 싱글톤

## Git Workflow

**NEVER commit directly to main/master branch.** Always use feature branches.

```bash
# 브랜치 생성
git checkout main && git pull origin main
git checkout -b feature/{issue-number}-{name}   # 새 기능
git checkout -b fix/{issue-number}-{name}       # 버그 수정 (hotfix 포함)
```

- PR 생성 후 merge (직접 push 금지)
- hotfix도 반드시 `fix/` 브랜치 → PR → merge

## Environment Variables

`backend/.env.example` 참조. 필수: `OPENAI_API_KEY`, `RAG_INDEX_TOKEN`

## Tech Stack Summary

| 구분 | 스택 |
|------|------|
| Frontend | Next.js 16, React 19, shadcn/ui, Tailwind CSS 4, TypeScript |
| Backend | FastAPI, LangChain, ChromaDB, OpenAI (gpt-4o-mini) |
| Package | npm (frontend), uv (backend) |
| 배포 | Docker (multi-platform arm64/amd64), GitHub Actions |
