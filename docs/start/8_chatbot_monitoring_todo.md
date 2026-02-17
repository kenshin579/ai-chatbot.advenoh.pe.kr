# RAG 챗봇 모니터링 - TODO 체크리스트

## M1: Liquibase 스키마 + PreSync Job + `/chat` 로깅 연동

### Backend - Liquibase 설정
- [x] `backend/liquibase/` 디렉토리 구조 생성
- [x] `backend/liquibase/changelog.yaml` - 메인 changelog 설정 (includeAll, NaturalOrderComparator)
- [x] `backend/liquibase/liquibase.properties` - 로컬 개발용 설정
- [x] `backend/liquibase/lib/` - mysql-connector-j-8.4.0.jar, liquibase-natural-comparator.jar 복사
- [x] `backend/liquibase/changes/2026-02/1-create_query_logs.sql` - query_logs 테이블 (rollback 포함)
- [x] `backend/liquibase/changes/2026-02/2-create_feedbacks.sql` - feedbacks 테이블 (rollback 포함)
- [x] `backend/Dockerfile` - liquibase 파일을 `/liquibase/` 경로에 COPY 추가

### MySQL DB 수동 생성 (배포 전 1회 실행)

```bash
kubectl exec -it -n app mysql-0 -- mysql -u root -p'<ROOT_PASSWORD>'
```

```sql
CREATE DATABASE IF NOT EXISTS `ai_chatbot`
CHARACTER SET utf8mb4
COLLATE utf8mb4_0900_ai_ci;

CREATE USER IF NOT EXISTS 'ai_chatbot'@'%'
IDENTIFIED WITH mysql_native_password
BY '<USER_PASSWORD>';

GRANT ALL PRIVILEGES ON `ai_chatbot`.* TO 'ai_chatbot'@'%';

FLUSH PRIVILEGES;

-- 확인
SHOW DATABASES;
SELECT user, host FROM mysql.user WHERE user = 'ai_chatbot';
```

> **Note**: 실제 비밀번호는 `charts/mysql/values.yaml` 참조

### Charts - MySQL initdbScripts 추가 (향후 재생성 대비)
- [ ] `charts/mysql/values.yaml` - `ai_chatbot` DB 및 사용자를 initdbScripts에 추가

### Charts - ai-chatbot-be PreSync Job
- [ ] `charts/ai-chatbot-be/values.yaml` - MySQL 연결 설정 + liquibase 설정 추가
- [ ] `charts/ai-chatbot-be/templates/secret.yaml` - PreSync 어노테이션(wave 0) + MySQL/ADMIN_TOKEN 추가
- [ ] `charts/ai-chatbot-be/templates/configmap.yaml` - MYSQL_HOST, MYSQL_PORT, MYSQL_DATABASE 환경변수 추가
- [ ] `charts/ai-chatbot-be/templates/presync-liquibase.yaml` - 신규 생성 (inspireme-be 패턴 참고)
  - [ ] initContainer 1: copy-changelog (앱 이미지에서 changelog/lib 복사)
  - [ ] initContainer 2: run-liquibase (liquibase status + update)
  - [ ] container: placeholder (email 비활성화 시)

### Backend - DB 모듈
- [x] `pyproject.toml` - `sqlalchemy[asyncio]`, `aiomysql` 의존성 추가
- [x] `app/db/__init__.py` 생성
- [x] `app/db/connection.py` - AsyncEngine, async_sessionmaker 설정
- [x] `app/db/models.py` - QueryLog, Feedback ORM 모델
- [x] `app/db/repository.py` - QueryLogRepository 클래스 (save_query_log)
- [x] `app/config.py` - MySQL 관련 설정 추가 (mysql_host, mysql_port, mysql_database, mysql_user, mysql_password, database_url)
- [x] `app/main.py` - lifespan에 init_db/close_db 추가

### Backend - /chat 로깅
- [x] `app/api/routes.py` - /chat 엔드포인트에 응답 시간 측정 추가
- [x] `app/api/routes.py` - /chat 엔드포인트에 query_logs 테이블 저장 로직 추가
- [x] `app/api/models.py` - ChatResponse에 `message_id` 필드 추가

### 테스트
- [ ] 로컬 MySQL + Liquibase로 스키마 생성 확인
- [ ] /chat 호출 → query_logs 테이블 기록 확인
- [ ] Docker 이미지 빌드 → PreSync Job 실행 → 테이블 생성 확인

---

## M2: 사용자 피드백 API + LangSmith 연동

### Backend - /feedback API
- [ ] `app/api/models.py` - FeedbackRequest 모델 추가
- [ ] `app/api/routes.py` - POST /feedback 엔드포인트 구현
- [ ] `app/db/repository.py` - save_feedback 메서드 추가
- [ ] LangSmith Feedback API 연동 (langsmith Client.create_feedback)

### Charts - Gateway 라우트
- [ ] `charts/gateway/values.yaml` - `/feedback` 라우트 추가 (→ ai-chatbot-be-service)

### 테스트
- [ ] POST /feedback API 호출 → feedbacks 테이블 저장 확인
- [ ] LangSmith 대시보드에서 피드백 데이터 확인

---

## M3: 채팅 UI에 피드백 버튼 추가

### Frontend - API 클라이언트
- [ ] `src/lib/api.ts` - ChatResponse에 message_id 추가
- [ ] `src/lib/api.ts` - FeedbackRequest 인터페이스, sendFeedback 함수 추가

### Frontend - 피드백 UI
- [ ] `src/components/MessageList.tsx` - AI 메시지 하단에 👍👎 버튼 추가
- [ ] 피드백 전송 후 버튼 비활성화 (중복 방지)
- [ ] 피드백 전송 상태 표시 (로딩, 완료)

### 테스트 (MCP Playwright)
- [ ] 채팅 응답 후 👍👎 버튼 렌더링 확인
- [ ] 👍 클릭 → POST /feedback 호출 확인
- [ ] 클릭 후 버튼 비활성화 확인

---

## M4: Admin 통계 API

### Backend - /admin/stats API
- [ ] `app/config.py` - admin_token 설정 추가
- [ ] `app/api/routes.py` - verify_admin_token 의존성 함수
- [ ] `app/api/routes.py` - GET /admin/stats 엔드포인트 구현
- [ ] `app/db/repository.py` - get_daily_counts (일별 질문 수)
- [ ] `app/db/repository.py` - get_top_questions (인기 질문 TOP 10)
- [ ] `app/db/repository.py` - get_feedback_ratio (👍👎 비율)
- [ ] `app/db/repository.py` - get_avg_response_time (평균 응답 시간)
- [ ] `app/db/repository.py` - get_search_failure_rate (검색 실패율)

### Charts
- [ ] `charts/ai-chatbot-be/templates/secret.yaml` - ADMIN_TOKEN 추가
- [ ] `charts/gateway/values.yaml` - `/admin/stats` 라우트 추가

### 테스트
- [ ] GET /admin/stats (토큰 없음) → 401 확인
- [ ] GET /admin/stats (유효 토큰) → 통계 데이터 반환 확인

---

## M5: Admin 대시보드 페이지 + 차트

### Frontend - 의존성
- [ ] `package.json` - recharts 추가 (`npm install recharts`)

### Frontend - API 클라이언트
- [ ] `src/lib/api.ts` - AdminStats 인터페이스, getAdminStats 함수 추가

### Frontend - Admin 컴포넌트
- [ ] `src/components/admin/StatsCard.tsx` - 통계 카드 (질문 수, 피드백 점수, 응답 시간, 실패율)
- [ ] `src/components/admin/QueryChart.tsx` - 일별 질문 수 LineChart (recharts)
- [ ] `src/components/admin/TopQuestions.tsx` - 인기 질문 테이블
- [ ] `src/components/admin/CollectionInfo.tsx` - 인덱싱 현황

### Frontend - Admin 페이지
- [ ] `src/app/admin/page.tsx` - 토큰 입력 → 통계 조회 → 대시보드 렌더링

### 테스트 (MCP Playwright)
- [ ] `/admin` 페이지 접근 → 토큰 입력 UI 확인
- [ ] 토큰 입력 후 통계 데이터 렌더링 확인
- [ ] 차트/카드 컴포넌트 정상 표시 확인

---

## 배포

- [ ] Backend Docker 이미지 빌드 및 푸시 (`kenshin579/ai-chatbot-be:<new-version>`)
- [ ] Frontend Docker 이미지 빌드 및 푸시 (`kenshin579/ai-chatbot-fe:<new-version>`)
- [ ] Charts 버전 업데이트 (ai-chatbot-be, ai-chatbot-fe values.yaml)
- [ ] PR 생성 → main merge → release 브랜치 푸시
- [ ] ArgoCD sync 확인
