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
