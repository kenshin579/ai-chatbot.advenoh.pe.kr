# 헤더 네비게이션 개선 PRD

## 1. 개요

### 1.1 목적

`ai-chatbot.advenoh.pe.kr`의 헤더를 개선하여 Admin 대시보드 접근성과 외부 블로그 이동 링크를 추가한다.

### 1.2 현재 문제

- Admin 페이지(`/admin`)가 직접 URL 입력으로만 접근 가능 (네비게이션 링크 없음)
- 실제 블로그 사이트로 이동할 수 있는 링크가 없음
- 헤더가 `ChatWindow` 컴포넌트 내부에 인라인으로 구현되어 있어 재사용 불가

### 1.3 관련 Repo

- **Repo**: [ai-chatbot.advenoh.pe.kr](https://github.com/kenshin579/ai-chatbot.advenoh.pe.kr)
- Frontend: `frontend/` (Next.js)

---

## 2. 현재 구조 분석

### 2.1 현재 헤더 (ChatWindow.tsx 인라인)

```
┌─────────────────────────────────────────────┐
│  Blog Q&A Chatbot              [IT Blog ▼]  │
└─────────────────────────────────────────────┘
```

- 왼쪽: 제목 텍스트
- 오른쪽: 블로그 선택 드롭다운 (IT Blog / Investment Blog)
- Admin 링크 없음, 외부 블로그 링크 없음

### 2.2 관련 파일

| 파일 | 역할 |
|------|------|
| `frontend/src/components/ChatWindow.tsx` | 헤더가 인라인으로 포함됨 (line 76~90) |
| `frontend/src/app/layout.tsx` | Root 레이아웃 (헤더 없음) |
| `frontend/src/app/page.tsx` | 메인 페이지 (ChatWindow 렌더링) |
| `frontend/src/app/admin/page.tsx` | Admin 대시보드 (독립 페이지, 네비게이션 없음) |

### 2.3 사용 중인 UI 라이브러리

- shadcn/ui (Radix UI) + Tailwind CSS 4
- 기존 컴포넌트: Button, Select, Card, Input, ScrollArea

---

## 3. 목표 UI

```
┌──────────────────────────────────────────────────────────────┐
│  Blog Q&A Chatbot    [IT Blog ▼]          [Admin]  [☰ 메뉴] │
└──────────────────────────────────────────────────────────────┘
```

### 3.1 헤더 구성 요소

| 위치 | 요소 | 동작 |
|------|------|------|
| 왼쪽 | "Blog Q&A Chatbot" 제목 | 클릭 시 `/` (채팅 메인)으로 이동 |
| 중앙-왼쪽 | 블로그 선택 드롭다운 | 기존 기능 유지 (IT Blog / Investment Blog) |
| 오른쪽 | "Admin" 링크 | 클릭 시 `/admin` 페이지로 이동 |
| 맨 오른쪽 | 메뉴 드롭다운 | 외부 블로그 링크 목록 표시 |

### 3.2 메뉴 드롭다운 항목

| 항목 | URL | 비고 |
|------|-----|------|
| IT Blog | `https://blog-v2.advenoh.pe.kr` | 새 탭에서 열기 |
| Investment Blog | `https://investment.advenoh.pe.kr` | 새 탭에서 열기 |

---

## 4. 요구사항

### 4.1 Header 컴포넌트 분리

**현재**: `ChatWindow.tsx` 내부에 인라인으로 구현
**변경**: 별도 `Header` 컴포넌트로 분리

- **신규 파일**: `frontend/src/components/Header.tsx`
- **수정 파일**: `frontend/src/app/layout.tsx` — Header를 공통 레이아웃에 배치
- **수정 파일**: `frontend/src/components/ChatWindow.tsx` — 인라인 헤더 제거

### 4.2 공통 레이아웃 적용

Header를 `layout.tsx`에 배치하여 모든 페이지(`/`, `/admin`)에서 동일한 헤더를 표시한다.

```
layout.tsx
├── Header (공통)
├── children
│   ├── / → ChatWindow (헤더 없는 채팅 영역)
│   └── /admin → AdminPage (헤더 없는 대시보드)
```

### 4.3 Admin 링크

- 헤더 오른쪽에 "Admin" 텍스트 링크 또는 버튼 배치
- Next.js `<Link>` 사용 (클라이언트 네비게이션)
- 현재 페이지가 `/admin`일 때 활성 상태 스타일 적용

### 4.4 외부 블로그 링크 메뉴

- 헤더 맨 오른쪽에 메뉴 아이콘 (햄버거 또는 점 3개) 배치
- 클릭 시 드롭다운 메뉴 표시
- 외부 링크는 `target="_blank"` + `rel="noopener noreferrer"` 적용
- shadcn/ui `DropdownMenu` 컴포넌트 활용

### 4.5 블로그 선택 드롭다운 위치

- 블로그 선택 드롭다운은 채팅 기능 전용이므로 `/admin` 페이지에서는 숨김
- `/` 페이지에서만 표시되도록 조건부 렌더링
- 방법 A: Header에서 현재 경로를 확인하여 조건부 렌더링
- 방법 B: 블로그 선택 드롭다운은 ChatWindow에 그대로 유지

### 4.6 Admin 페이지 뒤로가기

- Admin 페이지에서도 헤더가 표시되므로 제목 클릭으로 메인 채팅 페이지로 복귀 가능

---

## 5. 수용 기준

- [ ] 메인 페이지(`/`)에서 Admin 링크 클릭 시 `/admin` 페이지로 이동
- [ ] Admin 페이지에서 제목 클릭 시 메인 페이지(`/`)로 복귀
- [ ] 헤더 메뉴에서 IT Blog 클릭 시 `blog-v2.advenoh.pe.kr`이 새 탭에서 열림
- [ ] 헤더 메뉴에서 Investment Blog 클릭 시 `investment.advenoh.pe.kr`이 새 탭에서 열림
- [ ] 블로그 선택 드롭다운이 메인 페이지에서 정상 동작
- [ ] 모바일에서 헤더 레이아웃이 깨지지 않음
