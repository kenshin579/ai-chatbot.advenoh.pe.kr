import logging

import httpx
from langchain_core.documents import Document

logger = logging.getLogger(__name__)

INSPIREME_URL = "https://inspireme.advenoh.pe.kr"

PAGE_SIZE = 1000


def _build_quote_document(quote: dict) -> Document:
    """명언 API 응답을 LangChain Document로 변환한다."""
    content_parts = []

    if quote.get("content"):
        content_parts.append(f'"{quote["content"]}"')
    for t in quote.get("translations", []):
        if t.get("content"):
            content_parts.append(f'"{t["content"]}"')

    author_name = quote.get("author", "Unknown")
    author_info = quote.get("authorInfo") or {}
    content_parts.append(f"— {author_name}")

    topics = quote.get("topics") or []
    tags = quote.get("tags") or []
    if topics:
        content_parts.append(f"주제: {', '.join(topics)}")
    if tags:
        content_parts.append(f"태그: {', '.join(tags)}")
    if author_info.get("bio"):
        content_parts.append(f"저자 소개: {author_info['bio']}")

    page_content = "\n".join(content_parts)

    metadata = {
        "blog_id": "inspireme",
        "type": "quote",
        "quote_id": quote["id"],
        "author": author_name,
        "url": f"{INSPIREME_URL}/quotes/{quote['id']}",
    }
    if author_info.get("slug"):
        metadata["author_slug"] = author_info["slug"]
    if topics:
        metadata["topics"] = topics
    if tags:
        metadata["tags"] = tags

    return Document(page_content=page_content, metadata=metadata)


def _build_author_document(author_ko: dict, author_en: dict | None = None) -> Document:
    """저자 API 응답(ko/en)을 LangChain Document로 변환한다."""
    name_ko = author_ko.get("name", "Unknown")
    name_en = author_en.get("name", "") if author_en else ""

    content_parts = []
    if name_en:
        content_parts.append(f"{name_ko} ({name_en})")
    else:
        content_parts.append(name_ko)

    if author_ko.get("nationality"):
        content_parts.append(f"국적: {author_ko['nationality']}")
    if author_ko.get("birthYear"):
        birth = f"출생: {author_ko['birthYear']}"
        if author_ko.get("deathYear"):
            birth += f", 사망: {author_ko['deathYear']}"
        content_parts.append(birth)
    if author_ko.get("bio"):
        content_parts.append(f"소개: {author_ko['bio']}")
    if author_en and author_en.get("bio"):
        content_parts.append(f"Bio: {author_en['bio']}")

    page_content = "\n".join(content_parts)

    slug = author_ko.get("slug", "")
    metadata = {
        "blog_id": "inspireme",
        "type": "author",
        "author_id": author_ko["id"],
        "author_slug": slug,
        "url": f"{INSPIREME_URL}/authors/{slug}",
    }

    return Document(page_content=page_content, metadata=metadata)


async def _fetch_all_quotes(client: httpx.AsyncClient) -> list[dict]:
    """명언 목록을 페이지네이션하여 전체 로드한다."""
    all_quotes = []
    offset = 0
    while True:
        resp = await client.get("/api/quotes", params={"limit": PAGE_SIZE, "offset": offset})
        resp.raise_for_status()
        quotes = resp.json()
        all_quotes.extend(quotes)
        if len(quotes) < PAGE_SIZE:
            break
        offset += PAGE_SIZE
    return all_quotes


async def _fetch_all_authors(client: httpx.AsyncClient, lang: str) -> dict[str, dict]:
    """저자 목록을 페이지네이션하여 전체 로드한다. {id: author_dict} 반환."""
    authors = {}
    offset = 0
    while True:
        resp = await client.get("/api/authors", params={"lang": lang, "limit": PAGE_SIZE, "offset": offset})
        resp.raise_for_status()
        data = resp.json()
        for a in data.get("authors", []):
            authors[a["id"]] = a
        if offset + PAGE_SIZE >= data.get("total", 0):
            break
        offset += PAGE_SIZE
    return authors


async def load_inspireme_documents(api_url: str) -> list[Document]:
    """inspireme API에서 명언/저자 데이터를 로드하여 Document 리스트로 반환한다."""
    documents = []

    async with httpx.AsyncClient(base_url=api_url, timeout=60.0) as client:
        quotes = await _fetch_all_quotes(client)
        for quote in quotes:
            documents.append(_build_quote_document(quote))
        logger.info(f"명언 {len(quotes)}개 로드 완료")

        authors_ko = await _fetch_all_authors(client, "ko")
        authors_en = await _fetch_all_authors(client, "en")

        for author_id, author_ko in authors_ko.items():
            author_en = authors_en.get(author_id)
            documents.append(_build_author_document(author_ko, author_en))
        logger.info(f"저자 {len(authors_ko)}명 로드 완료")

    logger.info(f"총 {len(documents)}개 Document 생성")
    return documents
