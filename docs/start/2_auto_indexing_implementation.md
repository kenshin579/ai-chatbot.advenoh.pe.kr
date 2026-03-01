# 자동 인덱싱 CronJob - 구현 계획서

## 1. 프로젝트 구조 변경

### 1.1 ai-chatbot Backend 수정/신규 파일

```
ai-chatbot.advenoh.pe.kr/backend/
├── app/
│   └── api/
│       └── routes.py              # /index/{blog_id} — git clone 방식으로 통일
├── scripts/
│   └── cron_reindex.sh            # 신규: 수동 테스트용 인덱싱 스크립트
└── Dockerfile                     # git 패키지 설치 추가
```

### 1.2 Charts 신규/수정 파일

```
charts/
├── bootstrap/
│   └── macmini-app.yaml                    # ai-chatbot-reindex 엔트리 추가
└── charts/
    └── cronjob/
        └── ai-chatbot-reindex/             # 신규 Helm 차트
            ├── Chart.yaml
            ├── values.yaml
            └── templates/
                ├── cronjob.yaml
                └── secret.yaml
```

---

## 2. ai-chatbot Backend 구현

### 2.1 `/index/{blog_id}` API 개선 (`app/api/routes.py`)

현재 상대 경로 하드코딩(`../../blog-v2.advenoh.pe.kr/contents/`)을 **git clone 방식으로 통일**한다. 로컬/K8s 환경 구분 없이 항상 git clone으로 소스를 가져온다.

```python
import shutil
import subprocess
import tempfile

BLOG_REPOS = {
    "blog-v2": "https://github.com/kenshin579/blog-v2.advenoh.pe.kr.git",
    "investment": "https://github.com/kenshin579/investment.advenoh.pe.kr.git",
}

@router.post("/index/{blog_id}", response_model=IndexResponse)
async def reindex(
    blog_id: str,
    _token: str = Depends(verify_index_token),
    settings: Settings = Depends(get_settings),
    manager: VectorStoreManager = Depends(get_vector_store_manager),
):
    """블로그 문서 전체 재인덱싱 (Bearer 토큰 인증 필요)"""
    if blog_id not in settings.blog_collections:
        raise HTTPException(status_code=400, detail=f"Unknown blog_id: {blog_id}")

    if blog_id not in BLOG_REPOS:
        raise HTTPException(status_code=400, detail=f"No repository for: {blog_id}")

    manager.delete_collection(blog_id)

    clone_dir = tempfile.mkdtemp(prefix=f"reindex-{blog_id}-")
    try:
        # 1. git clone으로 블로그 소스 가져오기
        subprocess.run(
            ["git", "clone", "--depth", "1", BLOG_REPOS[blog_id], clone_dir],
            check=True,
            capture_output=True,
        )
        contents_dir = f"{clone_dir}/contents/"

        # 2. 인덱싱
        documents = load_blog_documents(contents_dir, blog_id)
        chunks = split_documents(documents, settings.chunk_size, settings.chunk_overlap)
        indexed = manager.index_documents(blog_id, chunks)
    finally:
        # 3. 임시 디렉토리 정리
        shutil.rmtree(clone_dir, ignore_errors=True)

    return IndexResponse(status="ok", blog_id=blog_id, indexed_chunks=indexed)
```

**핵심 변경사항**:
- 로컬/K8s 환경 구분 없이 항상 `git clone --depth 1`로 shallow clone 후 인덱싱
- 코드 경로가 하나이므로 유지보수 및 디버깅이 간단
- `tempfile.mkdtemp()`로 임시 디렉토리 생성 → finally에서 정리

### 2.2 Dockerfile 수정

git 명령어가 필요하므로 런타임 이미지에 git 설치를 추가한다.

```dockerfile
FROM python:3.12-slim AS builder
WORKDIR /app
COPY pyproject.toml ./
RUN pip install --no-cache-dir uv && \
    uv pip install --system --no-cache .

FROM python:3.12-slim
RUN apt-get update && apt-get install -y --no-install-recommends git && rm -rf /var/lib/apt/lists/*
WORKDIR /app
COPY --from=builder /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin
COPY app/ ./app/
COPY liquibase/changelog.yaml /liquibase/changelog/changelog.yaml
COPY liquibase/changes/ /liquibase/changelog/changes/
COPY liquibase/lib/ /liquibase/lib/
EXPOSE 8080
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8080"]
```

### 2.3 수동 테스트용 스크립트 (`scripts/cron_reindex.sh`)

```bash
#!/bin/bash
# 모든 블로그 순차 재인덱싱 (수동 테스트용)
set -euo pipefail

API_URL="${AI_CHATBOT_API_URL:-http://localhost:8080}"
TOKEN="${RAG_INDEX_TOKEN:?RAG_INDEX_TOKEN 환경변수 필요}"

for BLOG_ID in blog-v2 investment; do
  echo "[$(date)] Reindexing ${BLOG_ID}..."
  HTTP_STATUS=$(curl -s -o /tmp/response.json -w "%{http_code}" \
    -X POST "${API_URL}/index/${BLOG_ID}" \
    -H "Authorization: Bearer ${TOKEN}" \
    -H "Content-Type: application/json" \
    --max-time 600)

  if [ "$HTTP_STATUS" -eq 200 ]; then
    echo "[$(date)] ${BLOG_ID} 인덱싱 성공: $(cat /tmp/response.json)"
  else
    echo "[$(date)] ${BLOG_ID} 인덱싱 실패 (HTTP ${HTTP_STATUS}): $(cat /tmp/response.json)"
    exit 1
  fi
done

echo "[$(date)] 전체 인덱싱 완료"
```

---

## 3. Charts — K8s CronJob Helm 차트

### 3.1 Chart.yaml

```yaml
apiVersion: v2
name: ai-chatbot-reindex
description: AI Chatbot 블로그 자동 재인덱싱 CronJob
version: 0.1.0
```

### 3.2 values.yaml

```yaml
namespace: app
application: ai-chatbot-reindex

image:
  name_tag: curlimages/curl:8.5.0
  pullPolicy: IfNotPresent

cronjob:
  name: ai-chatbot-reindex-cronjob
  schedule: "0 18 * * 0"  # 매주 일요일 03:00 KST (UTC 토요일 18:00)

cronjobDefaults:
  activeDeadlineSeconds: 1800  # 30분
  backoffLimit: 1
  successfulJobsHistoryLimit: 3
  failedJobsHistoryLimit: 3

config:
  apiUrl: "http://ai-chatbot-be-service.app.svc.cluster.local"
  blogIds: "blog-v2,investment"

secrets:
  ragIndexToken: "909d918aad716b761bd39a8e40f70a2e077a7f1039f1aa0b521c9e3a2e999c28"
```

**주요 설정**:
- `curlimages/curl` — 경량 curl 이미지 사용 (CronJob은 API 호출만 수행)
- `apiUrl` — K8s 클러스터 내부 서비스 DNS (`ai-chatbot-be-service.app.svc.cluster.local`)
- `schedule` — UTC 기준 `0 18 * * 0` = KST 일요일 03:00
- `activeDeadlineSeconds: 1800` — 최대 30분 (인덱싱 시간 고려)
- `blogIds` — 쉼표 구분 블로그 ID 목록 (CronJob 스크립트에서 순차 처리)

### 3.3 templates/secret.yaml

```yaml
apiVersion: v1
kind: Secret
metadata:
  name: {{ .Values.application }}-secret
  namespace: {{ .Values.namespace }}
type: Opaque
stringData:
  RAG_INDEX_TOKEN: {{ .Values.secrets.ragIndexToken | quote }}
```

### 3.4 templates/cronjob.yaml

```yaml
apiVersion: batch/v1
kind: CronJob
metadata:
  name: {{ .Values.cronjob.name }}
  namespace: {{ .Values.namespace }}
spec:
  schedule: {{ .Values.cronjob.schedule | quote }}
  concurrencyPolicy: Forbid
  startingDeadlineSeconds: 200
  jobTemplate:
    spec:
      activeDeadlineSeconds: {{ .Values.cronjobDefaults.activeDeadlineSeconds }}
      backoffLimit: {{ .Values.cronjobDefaults.backoffLimit }}
      template:
        spec:
          containers:
          - name: {{ .Values.application }}
            image: {{ .Values.image.name_tag }}
            command:
            - /bin/sh
            - -c
            - |
              for BLOG_ID in $(echo $BLOG_IDS | tr ',' ' '); do
                echo "[$(date)] Reindexing ${BLOG_ID}..."
                HTTP_STATUS=$(curl -s -o /tmp/resp.json -w "%{http_code}" \
                  -X POST "${API_URL}/index/${BLOG_ID}" \
                  -H "Authorization: Bearer ${RAG_INDEX_TOKEN}" \
                  -H "Content-Type: application/json" \
                  --max-time 600)
                if [ "$HTTP_STATUS" -eq 200 ]; then
                  echo "[$(date)] ${BLOG_ID} OK: $(cat /tmp/resp.json)"
                else
                  echo "[$(date)] ${BLOG_ID} FAIL (HTTP ${HTTP_STATUS}): $(cat /tmp/resp.json)"
                  exit 1
                fi
              done
              echo "[$(date)] All done"
            env:
            - name: API_URL
              value: {{ .Values.config.apiUrl | quote }}
            - name: BLOG_IDS
              value: {{ .Values.config.blogIds | quote }}
            - name: RAG_INDEX_TOKEN
              valueFrom:
                secretKeyRef:
                  name: {{ .Values.application }}-secret
                  key: RAG_INDEX_TOKEN
            resources:
              requests:
                memory: "64Mi"
                cpu: "100m"
              limits:
                memory: "128Mi"
                cpu: "200m"
          restartPolicy: OnFailure
  successfulJobsHistoryLimit: {{ .Values.cronjobDefaults.successfulJobsHistoryLimit }}
  failedJobsHistoryLimit: {{ .Values.cronjobDefaults.failedJobsHistoryLimit }}
```

### 3.5 ArgoCD ApplicationSet 등록 (`bootstrap/macmini-app.yaml`)

기존 `finance-apps` ApplicationSet의 elements에 추가:

```yaml
- name: ai-chatbot-reindex
  path: charts/cronjob/ai-chatbot-reindex
  namespace: app
```

---

## 4. 테스트

### 4.1 Backend 테스트

- `/index/blog-v2` API 호출 → git clone 방식으로 정상 인덱싱 확인
- `/index/investment` API 호출 → git clone 방식으로 정상 인덱싱 확인
- 잘못된 blog_id → 400 에러 반환 확인

### 4.2 Helm 차트 검증

```bash
cd charts/charts/cronjob/ai-chatbot-reindex
helm template . --debug
```

### 4.3 K8s 배포 후 검증

```bash
# CronJob 생성 확인
kubectl get cronjob -n app

# 수동 실행 테스트
kubectl create job --from=cronjob/ai-chatbot-reindex-cronjob test-reindex -n app

# 로그 확인
kubectl logs job/test-reindex -n app

# 완료 후 테스트 Job 정리
kubectl delete job test-reindex -n app
```
