# ai-chatbot.advenoh.pe.kr

RAG(Retrieval-Augmented Generation) 기반 블로그 Q&A 챗봇. 블로그 콘텐츠를 벡터 DB에 인덱싱하고, 사용자 질문에 대해 관련 문서를 검색하여 답변을 생성합니다.

## 기술 스택

| 구분 | 스택 |
|------|------|
| **Frontend** | Next.js 16, React 19, shadcn/ui, Tailwind CSS |
| **Backend** | FastAPI, LangChain, ChromaDB, OpenAI |
| **배포** | Docker (multi-platform), GitHub Actions, ArgoCD |

## 프로젝트 구조

```
ai-chatbot.advenoh.pe.kr/
├── frontend/          # Next.js 챗봇 UI
│   └── src/
│       ├── app/       # Next.js App Router
│       └── components/
├── backend/           # FastAPI RAG API 서버
│   ├── app/
│   │   ├── api/       # REST API 라우트
│   │   ├── rag/       # RAG 파이프라인 (chunker, embedder, retriever, chain)
│   │   ├── prompts/   # 프롬프트 템플릿
│   │   └── evaluation/# RAG 평가 (RAGAS)
│   ├── scripts/       # 문서 인덱싱 스크립트
│   └── tests/
├── scripts/           # 릴리스 및 Docker 푸시 스크립트
└── Makefile           # 통합 개발 명령어
```

## 시작하기

### 사전 요구사항

- Node.js 20+
- Python 3.12+
- [uv](https://docs.astral.sh/uv/) (Python 패키지 매니저)
- ChromaDB 서버 (기본: localhost:8000)

### 설치

```bash
# Backend 의존성
make install

# Frontend 의존성
cd frontend && npm install
```

### 환경 변수 설정

```bash
cp backend/.env.example backend/.env
```

주요 환경 변수:

| 변수 | 설명 | 기본값 |
|------|------|--------|
| `OPENAI_API_KEY` | OpenAI API 키 | - |
| `OPENAI_MODEL` | LLM 모델 | `gpt-4o-mini` |
| `EMBEDDING_MODEL` | 임베딩 모델 | `text-embedding-3-small` |
| `CHROMA_HOST` | ChromaDB 호스트 | `localhost` |
| `CHROMA_PORT` | ChromaDB 포트 | `8000` |

### 실행

```bash
# Frontend + Backend 동시 실행
make run-all

# 또는 개별 실행
make run-fe    # Frontend (포트 3000)
make run-be    # Backend  (포트 8080)
```

### 문서 인덱싱

```bash
# IT 블로그 문서 인덱싱
make index

# 투자 블로그 문서 인덱싱
make index-invest
```

## 개발

```bash
# 테스트
make test

# 린트
make lint

# 개발용 의존성 설치
make install-dev
```

## 배포

```bash
# Docker 이미지 빌드 및 푸시
make docker-push fe     # Frontend만
make docker-push be     # Backend만
make docker-push all    # 전체

# 버전 태그 생성 (GitHub Actions 릴리스 트리거)
make tag patch          # 패치 버전
make tag minor          # 마이너 버전
make tag major          # 메이저 버전
```

Docker 이미지:
- `kenshin579/ai-chatbot-fe` - Frontend
- `kenshin579/ai-chatbot-be` - Backend
