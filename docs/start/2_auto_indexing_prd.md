# 자동 인덱싱 CronJob - PRD

## 1. 배경

현재 ai-chatbot의 블로그 문서 인덱싱은 **수동으로만** 실행 가능하다.

- 로컬: `make index` / `make index-invest` (CLI 스크립트)
- 운영: `POST /index/{blog_id}` (Bearer 토큰 인증)

블로그에 새 글이 추가되거나 수정되어도 인덱싱을 직접 실행해야 하므로, ChromaDB의 데이터가 최신 상태가 아닐 수 있다. **주 1회 자동 인덱싱**을 통해 별도 수동 작업 없이 항상 최신 블로그 콘텐츠를 반영하도록 한다.

## 2. 현재 상태

| 항목 | 현재 값 |
|------|--------|
| 인덱싱 방식 | 수동 (CLI 또는 API 호출) |
| 대상 블로그 | `blog-v2` (IT 블로그), `investment` (투자 블로그) |
| API 엔드포인트 | `POST /index/{blog_id}` (Bearer 토큰 인증) |
| 소스 디렉토리 | `../../blog-v2.advenoh.pe.kr/contents/`, `../../investment.advenoh.pe.kr/contents/` |
| ChromaDB | `chromadb.app.svc.cluster.local:8000` (K8s 클러스터 내) |
| 인덱싱 토큰 | `RAG_INDEX_TOKEN` (Secret에 저장) |

## 3. 요구사항

### 3.1 주간 자동 인덱싱

매주 1회 자동으로 `blog-v2`, `investment` 블로그를 재인덱싱한다.

| 항목 | 값 |
|------|---|
| 스케줄 | 매주 일요일 03:00 KST (토요일 18:00 UTC) |
| 대상 | `blog-v2`, `investment` |
| 방식 | 기존 `POST /index/{blog_id}` API 호출 |
| 순서 | `blog-v2` 완료 후 `investment` 순차 실행 |

### 3.2 실행 방식 비교

| 방식 | 장점 | 단점 |
|------|------|------|
| **A. K8s CronJob (curl)** | 기존 stock-data-batch CronJob 패턴 재활용, 인프라 통합 관리 | 별도 Helm 차트 필요, curl 이미지 필요 |
| **B. GitHub Actions scheduled workflow** | 설정 간단, 별도 인프라 불필요 | GitHub에서 K8s 내부 서비스 접근 불가 (외부 도메인 필요) |
| **C. Backend 내장 스케줄러 (APScheduler)** | 별도 인프라 불필요, 코드 내 관리 | 백엔드 재시작 시 스케줄 리셋, 멀티 인스턴스 중복 실행 우려 |

**권장: 방식 A (K8s CronJob)** — 기존 `stock-data-batch` CronJob 차트 패턴과 동일하게 구성하면 일관성 있는 인프라 관리가 가능하다.

## 4. 해결해야 할 문제

### 4.1 /index API — 소스 디렉토리 경로 문제

현재 `/index/{blog_id}` API는 소스 디렉토리 경로가 **상대 경로로 하드코딩**되어 있다:

```python
# routes.py:135-138
contents_dirs = {
    "blog-v2": "../../blog-v2.advenoh.pe.kr/contents/",
    "investment": "../../investment.advenoh.pe.kr/contents/",
}
```

K8s 배포 환경에서는 이 경로에 블로그 소스가 존재하지 않으므로, `/index/{blog_id}` API는 **로컬 개발 환경에서만 동작**한다.

### 4.2 해결 방안: Git Clone Fallback

- 로컬 경로가 존재하면 기존처럼 직접 사용 (개발 환경 호환)
- 없으면 `git clone --depth 1`로 shallow clone 후 인덱싱 (K8s 환경)
- Dockerfile에 git 패키지 설치 필요

## 5. 구현 범위

| 영역 | 작업 |
|------|------|
| ai-chatbot Backend | `/index/{blog_id}` API git clone fallback 추가, Dockerfile git 설치 |
| Charts (신규) | `charts/cronjob/ai-chatbot-reindex/` Helm 차트 생성 |
| ArgoCD | `bootstrap/macmini-app.yaml`에 CronJob 엔트리 등록 |

상세 구현은 `2_auto_indexing_implementation.md` 참조.

## 6. 향후 개선 (선택)

| 항목 | 설명 |
|------|------|
| 실패 알림 | CronJob 실패 시 Slack/Discord 알림 (Grafana Alert Rule 활용) |
| 변경 감지 인덱싱 | 블로그 저장소 push 시 GitHub Actions webhook으로 즉시 인덱싱 |
| 증분 인덱싱 | 전체 재인덱싱 대신 변경된 문서만 업데이트 (성능 개선) |
| 인덱싱 히스토리 | 인덱싱 실행 이력을 DB에 저장 (시간, 문서 수, 성공/실패) |
