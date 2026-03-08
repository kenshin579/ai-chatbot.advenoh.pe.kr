# TODO: AI Chatbot 예시 질문 & 입력 UI 개선

## Step 1: 예시 질문 상수 파일 생성

- [x] `frontend/src/constants/sampleQuestions.ts` 생성
- [x] blog-v2, investment, inspireme 3개 블로그 예시 질문 정의

## Step 2: MessageList 빈 화면 UI 변경

- [x] `MessageList` props에 `onSampleClick` 콜백 추가
- [x] `SAMPLE_QUESTIONS` import
- [x] 빈 화면(messages.length === 0)을 아이콘 + 안내 메시지 + 예시 질문 카드 리스트로 교체
- [x] 예시 질문 카드 클릭 시 `onSampleClick(question)` 호출

## Step 3: ChatWindow 연결

- [x] `MessageList`에 `onSampleClick={handleSend}` prop 전달

## Step 4: ChatInput UI 개선

- [x] `border-t` 구분선 제거
- [x] 입력창 `rounded-full` + `shadow-sm` 적용
- [x] 전송 버튼을 입력창 내부 오른쪽에 Send 아이콘으로 변경
- [x] `max-w-2xl mx-auto`로 중앙 정렬 + 최대 너비 제한
- [x] placeholder를 `"블로그에 질문하기"`로 변경

## Step 5: 테스트 및 검증

- [ ] `npm run check` 타입 검사 통과
- [ ] MCP Playwright로 다음 항목 확인:
  - [ ] 초기 화면에 예시 질문 카드 4개 표시되는지
  - [ ] 예시 질문 카드 클릭 시 질문이 전송되는지
  - [ ] 대화 시작 후 예시 질문 카드가 사라지는지
  - [ ] 입력창이 둥근 모서리 + 내부 Send 아이콘으로 표시되는지
  - [ ] 블로그 전환(blog-v2 → investment → inspireme) 시 예시 질문이 변경되는지
  - [ ] 다크모드에서 카드/입력창 스타일 정상 표시되는지
