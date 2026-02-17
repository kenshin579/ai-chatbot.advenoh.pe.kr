# 헤더 네비게이션 개선 - TODO

## M1. 기반 작업

- [x] shadcn/ui DropdownMenu 컴포넌트 추가 (`npx shadcn@latest add dropdown-menu`)
- [x] `Header.tsx` 컴포넌트 생성 (제목 + Admin 링크 + 외부 링크 메뉴)
- [x] `layout.tsx`에 Header 컴포넌트 추가

## M2. 기존 코드 정리

- [x] `ChatWindow.tsx`에서 인라인 헤더 제거 (블로그 선택 드롭다운은 유지)
- [x] `page.tsx`에서 ChatWindow 높이 조정 (Header 높이 반영)
- [x] `admin/page.tsx`에서 `min-h-screen` 제거

## M3. 테스트 (MCP Playwright)

- [x] 메인 페이지에서 Admin 링크 클릭 → `/admin` 이동 확인
- [x] Admin 페이지에서 제목 클릭 → `/` 이동 확인
- [x] 외부 링크 메뉴에서 IT Blog 클릭 → 새 탭 열림 확인
- [x] 외부 링크 메뉴에서 Investment Blog 클릭 → 새 탭 열림 확인
- [x] 블로그 선택 드롭다운 정상 동작 확인
- [x] 모바일 뷰포트에서 헤더 레이아웃 확인
