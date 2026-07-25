#!/bin/bash
set -e

TARGET=${1:-all}
VERSION=$(git describe --tags --abbrev=0 2>/dev/null || echo "v0.0.0")
VERSION_NUM=${VERSION#v}
MAJOR_MINOR=$(echo $VERSION_NUM | cut -d. -f1,2)

COMMIT=$(git rev-parse --short HEAD 2>/dev/null || echo unknown)
# dirty 검사는 저장소 안일 때만 한다. 저장소가 아니면 git diff 가
# exit 129(확인 불가)를 돌려주므로, 그냥 || 로 쓰면 unknown-dirty 가 된다.
if git rev-parse --is-inside-work-tree >/dev/null 2>&1 && ! git diff --quiet HEAD 2>/dev/null; then
  COMMIT="${COMMIT}-dirty"
fi

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
  be)  build_and_push "ai-chatbot-be" "./backend" "--build-arg VERSION=${VERSION_NUM} --build-arg COMMIT=${COMMIT}" ;;
  all)
    build_and_push "ai-chatbot-be" "./backend" "--build-arg VERSION=${VERSION_NUM} --build-arg COMMIT=${COMMIT}"
    build_and_push "ai-chatbot-fe" "./frontend"
    ;;
  *) echo "Usage: $0 [fe|be|all]"; exit 1 ;;
esac
