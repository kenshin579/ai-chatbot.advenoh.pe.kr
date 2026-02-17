# 프롬프트 개선 TODO

## Phase 1: 코드 수정

- [x] `backend/app/prompts/templates.py` - SYSTEM_PROMPT 답변 스타일 규칙 개선
- [x] `backend/app/config.py` - 기본 모델 `gpt-4o-mini` → `gpt-4.1-nano` 변경
- [x] `backend/.env.example` - OPENAI_MODEL 기본값 업데이트

## Phase 2: 테스트 (MCP Playwright)

- [ ] 챗봇 사이트에서 "Claude Code Skill에 대해서 알려줘" 질문 → 대화형 답변 확인
- [ ] 답변에 원문의 `###` 헤더 구조가 그대로 복사되지 않는지 확인
- [ ] 답변이 컨텍스트에 없는 내용을 지어내지 않는지(hallucination) 확인
- [ ] 참고 글 출처(sources) 정상 표시 확인
- [ ] 대화 히스토리 기반 후속 질문 정상 동작 확인
- [ ] gpt-4.1-nano 모델 API 호출 정상 동작 확인
