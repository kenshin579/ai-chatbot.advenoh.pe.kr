# InspireMe 챗봇 - TODO 체크리스트

## M1: Document Loader — API → Document 변환 로직

### Backend - inspireme_loader.py

- [x] `app/rag/inspireme_loader.py` — 신규 파일 생성
  - [x] `_build_quote_document()` — 명언 API 응답 → Document 변환 (content + translations 포함)
  - [x] `_build_author_document()` — 저자 API 응답(ko/en) → Document 변환 (병합)
  - [x] `_fetch_all_quotes(client)` — 명언 목록 페이지네이션 전체 로드 (결과 < limit이면 종료)
  - [x] `_fetch_all_authors(client, lang)` — 저자 목록 페이지네이션 전체 로드 (total 기반 루프)
  - [x] `load_inspireme_documents(api_url)` — httpx로 inspireme API 호출 → Document 리스트 반환
    - [x] `GET /api/quotes?limit=100&offset=N` — 명언 페이지네이션 로드
    - [x] `GET /api/authors?lang=ko` + `lang=en` — 저자 페이지네이션 로드 후 id 기준 병합

### Backend - 의존성

- [x] `pyproject.toml` — `httpx` 의존성 추가

### Backend - 테스트

- [x] `tests/test_inspireme_loader.py` — 신규 테스트 파일
  - [x] `_build_quote_document()` — API 응답 → Document 변환 정확성 (page_content, metadata)
  - [x] `_build_author_document()` — ko/en 병합 변환 정확성
  - [x] 빈 번역/authorInfo 없는 경우 fallback
  - [x] URL 생성 정확성 (`/quotes/{id}`, `/authors/{slug}`)

---

## M2: 인덱싱 API 확장 + Config 추가

### Backend - config.py

- [x] `app/config.py` — `blog_collections`에 `"inspireme": "명언"` 추가
- [x] `app/config.py` — `inspireme_api_url: str = "http://localhost:8080"` 추가

### Backend - routes.py

- [x] `app/api/routes.py` — `/index/{blog_id}` 엔드포인트에 inspireme 분기 추가
  - [x] 기존 `BLOG_REPOS` git clone 분기 **앞에** `blog_id == "inspireme"` 분기 추가
  - [x] inspireme: `load_inspireme_documents(settings.inspireme_api_url)` 호출
  - [x] 청킹 없이 바로 `manager.index_documents()` 호출
  - [x] 기존 `elif blog_id in BLOG_REPOS` (git clone) / `else` (에러) 분기는 유지

### Backend - 환경변수

- [x] `backend/.env.example` — `INSPIREME_API_URL` 환경변수 추가
- [ ] `backend/.env` — 로컬 개발용 `INSPIREME_API_URL=http://localhost:8080` 설정

### Backend - 테스트

- [ ] `tests/test_api.py` — `POST /index/inspireme` 정상 인덱싱 확인 (mock httpx)
- [ ] 로컬 환경에서 inspireme 백엔드 실행 → API 호출 → 인덱싱 → ChromaDB 저장 확인

---

## M3: inspireme 전용 프롬프트 + 체인 분기

### Backend - 프롬프트

- [x] `app/prompts/templates.py` — `INSPIREME_SYSTEM_PROMPT` 추가
  - [x] 명언 추천 전문 AI 어시스턴트 역할 지정
  - [x] 원문 인용, 저자 명시, 공감 스타일 규칙
  - [x] 다국어 답변 (한국어 + 영어 원문 병기)

### Backend - 체인 분기

- [x] `app/rag/chain.py` — `create_rag_chain()`에 `blog_id` 파라미터 추가
  - [x] `blog_id == "inspireme"`이면 `INSPIREME_SYSTEM_PROMPT` 사용
  - [x] 그 외에는 기존 `SYSTEM_PROMPT` 사용
- [x] `app/api/routes.py` — `/chat` 엔드포인트에서 `create_rag_chain()` 호출 시 `blog_id` 전달

### Backend - 테스트

- [ ] `POST /chat { blog_id: "inspireme" }` → 명언 검색 + 답변 생성 확인
- [ ] 기존 blog-v2, investment chat이 정상 동작하는지 회귀 테스트

---

## M4: inspireme 프론트엔드 챗봇 UI

### Frontend - API 클라이언트

- [x] `lib/chatbot-api.ts` — 신규 파일 생성
  - [x] `ChatMessage`, `Source`, `ChatResponse`, `FeedbackRequest` 인터페이스
  - [x] `sendChat()` — POST /chatbot-api/chat 호출
  - [x] `sendFeedback()` — POST /chatbot-api/feedback 호출

### Frontend - Next.js 리라이트

- [x] `next.config.ts` — `/chatbot-api/:path*` → ai-chatbot 백엔드 리라이트 추가
  - [x] 환경변수: `CHATBOT_API_URL` (기본값: `http://localhost:8080`)

### Frontend - 챗봇 컴포넌트

- [x] `components/chatbot/ChatbotButton.tsx` — 플로팅 버튼
  - [x] 우측 하단 고정 (`fixed bottom-6 right-6 z-50`)
  - [x] `MessageCircle` 아이콘 (lucide-react)
  - [x] 클릭 시 ChatbotPanel 토글 (open/close 상태)
- [x] `components/chatbot/ChatbotPanel.tsx` — 챗봇 패널 메인 컨테이너
  - [x] 우측 하단 400×500px (`fixed bottom-20 right-6`)
  - [x] 헤더: "명언 AI 도우미" 타이틀 + X 닫기 버튼
  - [x] messages 상태 관리 (user + ai 메시지 배열)
  - [x] isLoading, error 상태 관리
  - [x] handleSend: chat_history 구성 + sendChat 호출
  - [x] ChatMessageList + ChatInput 합성
- [x] `components/chatbot/ChatMessageList.tsx` — 메시지 목록
  - [x] ScrollArea + 자동 하단 스크롤 (useRef + scrollIntoView)
  - [x] 사용자 메시지: 우측 정렬, 파란색 배경
  - [x] AI 메시지: 좌측 정렬, 회색 배경
  - [x] 출처 링크 표시 (title + url)
  - [x] 👍👎 피드백 버튼 (AI 메시지 하단)
  - [x] 피드백 전송 후 버튼 비활성화 + 확인 표시
  - [x] 로딩 상태: "답변을 생성하고 있습니다..." 펄스 애니메이션
  - [x] 초기 상태: 추천 질문 예시 표시
- [x] `components/chatbot/ChatInput.tsx` — 입력 폼
  - [x] Input + Send 버튼
  - [x] 엔터 키 제출 지원
  - [x] 로딩 중 비활성화
  - [x] placeholder: "명언에 대해 질문해 보세요..."

### Frontend - 레이아웃 통합

- [x] `app/layout.tsx` — ChatbotButton 컴포넌트 추가 (전체 페이지에 표시)

### 테스트 (MCP Playwright)

- [ ] inspireme 사이트에서 플로팅 버튼 렌더링 확인
- [ ] 버튼 클릭 → 챗봇 패널 열림/닫힘 확인
- [ ] 질문 입력 → API 호출 → 답변 표시 확인
- [ ] 출처 링크 클릭 → 명언 상세 페이지 이동 확인
- [ ] 👍👎 피드백 버튼 동작 확인

---

## M5: 피드백 연동 + 마무리

### Charts 변경

- [ ] `charts/ai-chatbot-be/values.yaml` — `config.inspiremeApiUrl` 추가
- [ ] `charts/ai-chatbot-be/templates/configmap.yaml` — `INSPIREME_API_URL` 환경변수 추가
- [ ] `charts/inspireme-fe/values.yaml` — CHATBOT_API_URL 환경변수 추가
- [ ] `charts/cronjob/ai-chatbot-reindex/values.yaml` — `config.blogIds`에 `inspireme` 추가 (`"blog-v2,investment,inspireme"`)

### 배포

- [ ] ai-chatbot Backend Docker 이미지 빌드 및 푸시
- [ ] inspireme Frontend Docker 이미지 빌드 및 푸시
- [ ] Charts 버전 업데이트 (ai-chatbot-be, inspireme-fe values.yaml)
- [ ] PR 생성 → main merge → release 브랜치 푸시
- [ ] ArgoCD sync 확인
- [ ] 운영 환경에서 inspireme 챗봇 동작 확인
