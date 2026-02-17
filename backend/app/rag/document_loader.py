import re
from pathlib import Path

import yaml
from langchain_core.documents import Document


def parse_frontmatter(content: str) -> tuple[dict, str]:
    """YAML frontmatter를 파싱하여 metadata와 본문을 분리한다."""
    pattern = r"^---\s*\n(.*?)\n---\s*\n(.*)$"
    match = re.match(pattern, content, re.DOTALL)
    if not match:
        return {}, content

    try:
        metadata = yaml.safe_load(match.group(1)) or {}
    except (yaml.YAMLError, ValueError):
        # YAML 파싱 오류 또는 날짜 형식 오류 시 빈 메타데이터 반환
        metadata = {}

    body = match.group(2)
    return metadata, body


def build_post_url(relative_path: str, blog_id: str) -> str:
    """블로그 글의 URL을 생성한다.

    예: go/go에서의-열거형-상수-enums-in-go/index.md
    → https://blog-v2.advenoh.pe.kr/go에서의-열거형-상수-enums-in-go
    """
    base_urls = {
        "blog-v2": "https://blog-v2.advenoh.pe.kr",
        "investment": "https://investment.advenoh.pe.kr",
    }
    base_url = base_urls.get(blog_id, "")

    # contents/go/go에서의-열거형/index.md → go에서의-열거형
    path = Path(relative_path)
    slug = path.parent.name
    return f"{base_url}/{slug}" if slug and slug != "." else base_url


def load_blog_documents(contents_dir: str, blog_id: str) -> list[Document]:
    """블로그 Markdown 파일을 로드하고 frontmatter를 metadata로 파싱한다."""
    contents_path = Path(contents_dir)
    if not contents_path.exists():
        raise FileNotFoundError(f"Contents directory not found: {contents_dir}")

    documents = []
    for md_file in sorted(contents_path.rglob("index.md")):
        try:
            content = md_file.read_text(encoding="utf-8")
            metadata, body = parse_frontmatter(content)
        except Exception as e:
            print(f"Warning: Failed to load {md_file}: {e}")
            continue

        # contents/ 기준 상대 경로
        relative_path = str(md_file.relative_to(contents_path))
        # 카테고리는 디렉토리 구조에서 추출 (예: go/, java/)
        parts = Path(relative_path).parts
        category = parts[0] if len(parts) > 1 else ""

        # ChromaDB는 빈 리스트를 허용하지 않으므로 필터링
        tags = metadata.get("tags", [])
        doc_metadata = {
            "blog_id": blog_id,
            "title": metadata.get("title", md_file.stem),
            "date": str(metadata.get("date", "")),
            "description": metadata.get("description", ""),
            "category": category,
            "source": relative_path,
            "url": build_post_url(relative_path, blog_id),
        }
        # tags가 비어있지 않은 경우에만 추가 (모두 문자열로 변환)
        if tags:
            doc_metadata["tags"] = [str(tag) for tag in tags]

        documents.append(Document(page_content=body, metadata=doc_metadata))

    return documents
