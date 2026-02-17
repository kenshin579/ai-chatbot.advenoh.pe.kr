# 헤더 네비게이션 개선 - 구현 계획

## 1. shadcn/ui DropdownMenu 추가

```bash
cd frontend && npx shadcn@latest add dropdown-menu
```

- `radix-ui` 패키지가 이미 설치되어 있으므로 CLI로 컴포넌트 파일만 생성
- 생성 파일: `frontend/src/components/ui/dropdown-menu.tsx`

---

## 2. Header 컴포넌트 생성

**파일**: `frontend/src/components/Header.tsx` (신규, Client Component)

### 2.1 구조

```tsx
"use client";

// 필요 import
import Link from "next/link";
import { usePathname } from "next/navigation";
import { Menu, ExternalLink } from "lucide-react";
import { DropdownMenu, DropdownMenuItem, ... } from "@/components/ui/dropdown-menu";
import { Button } from "@/components/ui/button";
```

### 2.2 레이아웃

```
┌──────────────────────────────────────────────────────────────┐
│  [Blog Q&A Chatbot]              [Admin]  [☰ 외부 링크 메뉴] │
└──────────────────────────────────────────────────────────────┘
```

| 영역 | 구현 |
|------|------|
| 제목 | `<Link href="/">Blog Q&A Chatbot</Link>` |
| Admin 링크 | `<Link href="/admin">Admin</Link>` — 현재 경로가 `/admin`이면 활성 스타일 |
| 외부 링크 메뉴 | `<DropdownMenu>` + `<Menu />` 아이콘 트리거 |

### 2.3 외부 블로그 링크 목록

```ts
const EXTERNAL_LINKS = [
  { label: "IT Blog", url: "https://blog-v2.advenoh.pe.kr" },
  { label: "Investment Blog", url: "https://investment.advenoh.pe.kr" },
];
```

- 각 항목: `<a href={url} target="_blank" rel="noopener noreferrer">`
- `ExternalLink` 아이콘을 라벨 옆에 표시

### 2.4 활성 경로 표시

```tsx
const pathname = usePathname();
// pathname === "/admin" → Admin 링크에 활성 스타일 (font-bold, underline 등)
```

---

## 3. layout.tsx 수정

**파일**: `frontend/src/app/layout.tsx`

### 변경 사항

```tsx
import { Header } from "@/components/Header";

export default function RootLayout({ children }) {
  return (
    <html lang="ko">
      <body className={...}>
        <Header />
        {children}
      </body>
    </html>
  );
}
```

- Header를 `{children}` 위에 배치
- Header가 모든 페이지(`/`, `/admin`)에서 공통으로 표시됨

---

## 4. ChatWindow.tsx 수정

**파일**: `frontend/src/components/ChatWindow.tsx`

### 변경 사항

인라인 헤더 영역(line 76~90) 제거:

```diff
  return (
    <div className="flex flex-col h-full">
-     {/* Header */}
-     <div className="flex items-center justify-between p-4 border-b">
-       <h1 className="text-lg font-semibold">Blog Q&A Chatbot</h1>
-       <Select value={blogId} onValueChange={setBlogId}>
-         ...
-       </Select>
-     </div>
+     {/* 블로그 선택 드롭다운 (채팅 영역 상단) */}
+     <div className="flex items-center justify-end p-2 border-b">
+       <Select value={blogId} onValueChange={setBlogId}>
+         ...
+       </Select>
+     </div>
```

- 제목과 네비게이션은 공통 Header로 이동
- 블로그 선택 드롭다운은 채팅 기능 전용이므로 ChatWindow에 유지
- 높이를 줄여 간결하게 표시 (`p-4` → `p-2`)

---

## 5. page.tsx 수정

**파일**: `frontend/src/app/page.tsx`

### 변경 사항

헤더 높이만큼 `h-screen`에서 빼야 함:

```diff
  export default function Home() {
    return (
-     <main className="h-screen">
+     <main className="h-[calc(100vh-3.5rem)]">
        <ChatWindow />
      </main>
    );
  }
```

- Header 높이(약 `3.5rem` = `h-14`)를 고려하여 ChatWindow 영역 계산

---

## 6. admin/page.tsx 수정

**파일**: `frontend/src/app/admin/page.tsx`

### 변경 사항

- 공통 Header가 적용되므로 `min-h-screen` 조정
- 기존 `<h1>Admin 대시보드</h1>` 유지 (페이지 내부 제목)

```diff
  return (
-   <div className="min-h-screen bg-background p-8">
+   <div className="bg-background p-8">
```
