#!/bin/bash
set -e

TARGET=${1:-all}
VERSION=$(git describe --tags --abbrev=0 2>/dev/null || echo "v0.0.0")
VERSION_NUM=${VERSION#v}
MAJOR_MINOR=$(echo $VERSION_NUM | cut -d. -f1,2)

REGISTRY=${DOCKER_REGISTRY:-docker.io}
USERNAME=${DOCKER_USERNAME:-kenshin579}

build_and_push() {
  local name=$1
  local context=$2
  local build_args=${3:-}
  local image="${REGISTRY}/${USERNAME}/${name}"

  echo "Building and pushing ${image}..."

  docker buildx build \
    --platform linux/arm64 \
    ${build_args} \
    --tag "${image}:${VERSION_NUM}" \
    --tag "${image}:${MAJOR_MINOR}" \
    --tag "${image}:latest" \
    --push \
    "${context}"

  echo "Successfully pushed ${image}"
}

case $TARGET in
  fe)  build_and_push "ai-chatbot-fe" "./frontend" ;;
  be)  build_and_push "ai-chatbot-be" "./backend" ;;
  all)
    build_and_push "ai-chatbot-be" "./backend"
    build_and_push "ai-chatbot-fe" "./frontend"
    ;;
  *) echo "Usage: $0 [fe|be|all]"; exit 1 ;;
esac
