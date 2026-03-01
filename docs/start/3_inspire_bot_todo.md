# InspireMe 챗봇 - TODO 체크리스트

## M1: Document Loader — DB → Document 변환 로직

### Backend - inspireme_loader.py

- [ ] `app/rag/inspireme_loader.py` — 신규 파일 생성
  - [ ] `QUOTES_QUERY` — quotes + quote_translations + authors + author_translations JOIN 쿼리
  - [ ] `AUTHORS_QUERY` — authors + author_translations JOIN 쿼리
  - [ ] `_build_quote_document()` — 명언 DB 레코드 → Document 변환 (ko/en 번역 포함)
  - [ ] `_build_author_document()` — 저자 DB 레코드 → Document 변환 (ko/en 번역 포함)
  - [ ] `load_inspireme_documents()` — DB 연결 → Document 리스트 반환

### Backend - 테스트

- [ ] `tests/test_inspireme_loader.py` — 신규 테스트 파일
  - [ ] `_build_quote_document()` 변환 정확성 (page_content, metadata)
  - [ ] `_build_author_document()` 변환 정확성
  - [ ] 다국어 번역 포함 여부 (ko + en 모두 page_content에 포함)
  - [ ] 빈 번역 처리 (content_ko 또는 content_en이 None인 경우 fallback)
  - [ ] URL 생성 정확성 (`/quotes/{id}`, `/authors/{slug}`)

---

## M2: 인덱싱 API 확장 + Config 추가

### Backend - config.py

- [ ] `app/config.py` — `blog_collections`에 `"inspireme": "명언"` 추가
- [ ] `app/config.py` — inspireme DB 접속 설정 추가
  - [ ] `inspireme_mysql_host`, `inspireme_mysql_port`, `inspireme_mysql_database`
  - [ ] `inspireme_mysql_user`, `inspireme_mysql_password`
  - [ ] `inspireme_database_url` 프로퍼티 추가

### Backend - routes.py

- [ ] `app/api/routes.py` — `/index/{blog_id}` 엔드포인트에 inspireme 분기 추가
  - [ ] `blog_id == "inspireme"`인 경우 `load_inspireme_documents()` 호출
  - [ ] 청킹 없이 바로 `index_documents()` 호출

### Backend - 환경변수

- [ ] `backend/.env.example` — INSPIREME_MYSQL_* 환경변수 추가
- [ ] `backend/.env` — 로컬 개발용 inspireme DB 접속 정보 설정

### Backend - 테스트

- [ ] `tests/test_api.py` — `POST /index/inspireme` 정상 인덱싱 확인 (mock DB)
- [ ] 로컬 환경에서 실제 inspireme DB 연결 → 인덱싱 → ChromaDB 저장 확인

---

## M3: inspireme 전용 프롬프트 + 체인 분기

### Backend - 프롬프트

- [ ] `app/prompts/templates.py` — `INSPIREME_SYSTEM_PROMPT` 추가
  - [ ] 명언 추천 전문 AI 어시스턴트 역할 지정
  - [ ] 원문 인용, 저자 명시, 공감 스타일 규칙
  - [ ] 다국어 답변 (한국어 + 영어 원문 병기)

### Backend - 체인 분기

- [ ] `app/rag/chain.py` — `create_rag_chain()`에 `blog_id` 파라미터 추가
  - [ ] `blog_id == "inspireme"`이면 `INSPIREME_SYSTEM_PROMPT` 사용
  - [ ] 그 외에는 기존 `SYSTEM_PROMPT` 사용
- [ ] `app/api/routes.py` — `/chat` 엔드포인트에서 `create_rag_chain()` 호출 시 `blog_id` 전달

### Backend - 테스트

- [ ] `POST /chat { blog_id: "inspireme" }` → 명언 검색 + 답변 생성 확인
- [ ] 기존 blog-v2, investment chat이 정상 동작하는지 회귀 테스트

---

## M4: inspireme 프론트엔드 챗봇 UI

### Frontend - API 클라이언트

- [ ] `lib/chatbot-api.ts` — 신규 파일 생성
  - [ ] `ChatMessage`, `Source`, `ChatResponse`, `FeedbackRequest` 인터페이스
  - [ ] `sendChat()` — POST /chatbot-api/chat 호출
  - [ ] `sendFeedback()` — POST /chatbot-api/feedback 호출

### Frontend - Next.js 리라이트

- [ ] `next.config.ts` — `/chatbot-api/:path*` → ai-chatbot 백엔드 리라이트 추가
  - [ ] 환경변수: `CHATBOT_API_URL` (기본값: `http://localhost:8080`)

### Frontend - 챗봇 컴포넌트

- [ ] `components/chatbot/ChatbotButton.tsx` — 플로팅 버튼
  - [ ] 우측 하단 고정 (`fixed bottom-6 right-6 z-50`)
  - [ ] `MessageCircle` 아이콘 (lucide-react)
  - [ ] 클릭 시 ChatbotPanel 토글 (open/close 상태)
- [ ] `components/chatbot/ChatbotPanel.tsx` — 챗봇 패널 메인 컨테이너
  - [ ] 우측 하단 400×500px (`fixed bottom-20 right-6`)
  - [ ] 헤더: "명언 AI 도우미" 타이틀 + X 닫기 버튼
  - [ ] messages 상태 관리 (user + ai 메시지 배열)
  - [ ] isLoading, error 상태 관리
  - [ ] handleSend: chat_history 구성 + sendChat 호출
  - [ ] ChatMessageList + ChatInput 합성
- [ ] `components/chatbot/ChatMessageList.tsx` — 메시지 목록
  - [ ] ScrollArea + 자동 하단 스크롤 (useRef + scrollIntoView)
  - [ ] 사용자 메시지: 우측 정렬, 파란색 배경
  - [ ] AI 메시지: 좌측 정렬, 회색 배경
  - [ ] 출처 링크 표시 (title + url)
  - [ ] 👍👎 피드백 버튼 (AI 메시지 하단)
  - [ ] 피드백 전송 후 버튼 비활성화 + 확인 표시
  - [ ] 로딩 상태: "답변을 생성하고 있습니다..." 펄스 애니메이션
  - [ ] 초기 상태: 추천 질문 예시 표시
- [ ] `components/chatbot/ChatInput.tsx` — 입력 폼
  - [ ] Input + Send 버튼
  - [ ] 엔터 키 제출 지원
  - [ ] 로딩 중 비활성화
  - [ ] placeholder: "명언에 대해 질문해 보세요..."

### Frontend - 레이아웃 통합

- [ ] `app/layout.tsx` — ChatbotButton 컴포넌트 추가 (전체 페이지에 표시)

### 테스트 (MCP Playwright)

- [ ] inspireme 사이트에서 플로팅 버튼 렌더링 확인
- [ ] 버튼 클릭 → 챗봇 패널 열림/닫힘 확인
- [ ] 질문 입력 → API 호출 → 답변 표시 확인
- [ ] 출처 링크 클릭 → 명언 상세 페이지 이동 확인
- [ ] 👍👎 피드백 버튼 동작 확인

---

## M5: 피드백 연동 + GitHub Actions + 마무리

### Charts 변경

- [ ] `charts/ai-chatbot-be/values.yaml` — inspireme MySQL 환경변수 추가
- [ ] `charts/ai-chatbot-be/templates/configmap.yaml` — INSPIREME_MYSQL_HOST/PORT/DATABASE 추가
- [ ] `charts/ai-chatbot-be/templates/secret.yaml` — INSPIREME_MYSQL_USER/PASSWORD 추가
- [ ] `charts/inspireme-fe/values.yaml` — CHATBOT_API_URL 환경변수 추가

### GitHub Actions (선택)

- [ ] `inspireme.advenoh.pe.kr/.github/workflows/reindex-chatbot.yml` — 재인덱싱 워크플로우
  - [ ] 트리거: push to main (backend/db/changes/** 변경 시)
  - [ ] 동작: `curl -X POST .../index/inspireme` + Bearer token

### 배포

- [ ] ai-chatbot Backend Docker 이미지 빌드 및 푸시
- [ ] inspireme Frontend Docker 이미지 빌드 및 푸시
- [ ] Charts 버전 업데이트 (ai-chatbot-be, inspireme-fe values.yaml)
- [ ] PR 생성 → main merge → release 브랜치 푸시
- [ ] ArgoCD sync 확인
- [ ] 운영 환경에서 inspireme 챗봇 동작 확인
