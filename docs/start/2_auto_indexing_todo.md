# 자동 인덱싱 CronJob - TODO 체크리스트

## 단계 1: ai-chatbot Backend — /index API 개선

### routes.py 수정

- [ ] `app/api/routes.py` — `/index/{blog_id}` 엔드포인트 git clone 방식으로 통일
  - [ ] `BLOG_REPOS` dict 추가 (blog-v2, investment GitHub URL)
  - [ ] 기존 `LOCAL_CONTENTS_DIRS` 상대 경로 하드코딩 제거
  - [ ] 항상 `git clone --depth 1`로 shallow clone 후 인덱싱
  - [ ] `tempfile.mkdtemp()`로 임시 디렉토리 생성
  - [ ] `finally`에서 `shutil.rmtree()` 정리

### Dockerfile 수정

- [ ] `backend/Dockerfile` — 런타임 이미지에 `git` 패키지 설치 추가
  - [ ] `RUN apt-get update && apt-get install -y --no-install-recommends git && rm -rf /var/lib/apt/lists/*`

### 인덱싱 스크립트

- [ ] `scripts/cron_reindex.sh` — 신규 파일 생성
  - [ ] `blog-v2`, `investment` 순차 API 호출
  - [ ] HTTP 상태 코드 확인 (200 아니면 exit 1)
  - [ ] `chmod +x` 실행 권한 설정

### 테스트

- [ ] 로컬 환경: git clone 방식으로 정상 인덱싱 동작 확인
- [ ] Docker 빌드 후 컨테이너 내에서 git 명령어 사용 가능 확인

### 빌드 & 푸시

- [ ] `make docker-push be` — 새 Docker 이미지 빌드 & 푸시
- [ ] `charts/ai-chatbot-be/values.yaml` — image.name_tag 버전 업데이트

---

## 단계 2: Charts — CronJob Helm 차트 생성

### Helm 차트 파일

- [ ] `charts/cronjob/ai-chatbot-reindex/Chart.yaml` — 차트 메타데이터
- [ ] `charts/cronjob/ai-chatbot-reindex/values.yaml` — CronJob 설정
  - [ ] `schedule: "0 18 * * 0"` (매주 일요일 03:00 KST)
  - [ ] `image: curlimages/curl:8.5.0`
  - [ ] `config.apiUrl`: K8s 내부 서비스 URL
  - [ ] `config.blogIds`: `blog-v2,investment`
  - [ ] `secrets.ragIndexToken`: 인덱싱 API 토큰
- [ ] `charts/cronjob/ai-chatbot-reindex/templates/secret.yaml` — RAG_INDEX_TOKEN Secret
- [ ] `charts/cronjob/ai-chatbot-reindex/templates/cronjob.yaml` — CronJob 리소스
  - [ ] blog ID 순차 순회 + curl API 호출
  - [ ] HTTP 상태 코드 검증 (200 아니면 exit 1)
  - [ ] `concurrencyPolicy: Forbid`
  - [ ] `activeDeadlineSeconds: 1800`

### Helm 검증

- [ ] `helm template . --debug` — YAML 생성 확인
- [ ] `helm lint .` — 차트 유효성 검증

### ArgoCD 등록

- [ ] `bootstrap/macmini-app.yaml` — `ai-chatbot-reindex` 엔트리 추가

---

## 단계 3: 배포 & 검증

### 배포

- [ ] ai-chatbot: PR 생성 → main merge → `make docker-push be`
- [ ] charts: PR 생성 → main merge → `git push origin main:release --force`
- [ ] ArgoCD sync 확인: `argocd app get ai-chatbot-reindex --refresh`

### 검증

- [ ] `kubectl get cronjob -n app` — CronJob 생성 확인
- [ ] `kubectl create job --from=cronjob/ai-chatbot-reindex-cronjob test-reindex -n app` — 수동 실행
- [ ] `kubectl logs job/test-reindex -n app` — 인덱싱 로그 확인
- [ ] 챗봇에서 최신 블로그 글 질문하여 답변 확인
- [ ] `kubectl delete job test-reindex -n app` — 테스트 Job 정리
