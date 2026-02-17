#!/bin/bash
set -e

VERSION_TYPE=${1:-minor}

# 최신 태그 가져오기
git fetch --tags
LATEST_TAG=$(git describe --tags --abbrev=0 2>/dev/null || echo "v0.0.0")
CURRENT_VERSION=${LATEST_TAG#v}

# 버전 파싱
IFS='.' read -r MAJOR MINOR PATCH <<< "$CURRENT_VERSION"

# 버전 범프
case $VERSION_TYPE in
  major) MAJOR=$((MAJOR + 1)); MINOR=0; PATCH=0 ;;
  minor) MINOR=$((MINOR + 1)); PATCH=0 ;;
  patch) PATCH=$((PATCH + 1)) ;;
  *) echo "Usage: $0 [patch|minor|major]"; exit 1 ;;
esac

NEW_VERSION="v${MAJOR}.${MINOR}.${PATCH}"

echo "Current version: $LATEST_TAG"
echo "New version: $NEW_VERSION"

# Git 태그 생성 및 푸시
git tag -a "$NEW_VERSION" -m "Release $NEW_VERSION"
git push origin "$NEW_VERSION"

# GitHub 릴리스 생성
gh release create "$NEW_VERSION" \
  --title "$NEW_VERSION" \
  --generate-notes

echo "Released: $NEW_VERSION"

# fe/be 동일 버전으로 Docker 이미지 빌드 및 푸시
echo "Building Docker images with version $NEW_VERSION..."
"$(dirname "$0")/docker-push.sh" all
