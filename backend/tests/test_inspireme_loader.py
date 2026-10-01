import httpx

from app.rag import inspireme_loader
from app.rag.inspireme_loader import (
    INSPIREME_URL,
    _build_author_document,
    _build_quote_document,
    load_inspireme_documents,
)


class TestBuildQuoteDocument:
    def test_basic_quote(self):
        quote = {
            "id": "quote-001",
            "content": "인생은 짧고 예술은 길다.",
            "author": "히포크라테스",
            "authorInfo": {"slug": "hippocrates", "bio": "고대 그리스 의학의 아버지"},
            "translations": [{"lang": "en", "content": "Life is short, art is long."}],
            "topics": ["인생", "지혜"],
            "tags": ["motivation", "wisdom"],
        }
        doc = _build_quote_document(quote)

        assert '"인생은 짧고 예술은 길다."' in doc.page_content
        assert '"Life is short, art is long."' in doc.page_content
        assert "— 히포크라테스" in doc.page_content
        assert "주제: 인생, 지혜" in doc.page_content
        assert "태그: motivation, wisdom" in doc.page_content
        assert "저자 소개: 고대 그리스 의학의 아버지" in doc.page_content

        assert doc.metadata["blog_id"] == "inspireme"
        assert doc.metadata["type"] == "quote"
        assert doc.metadata["quote_id"] == "quote-001"
        assert doc.metadata["author"] == "히포크라테스"
        assert doc.metadata["author_slug"] == "hippocrates"
        assert doc.metadata["topics"] == ["인생", "지혜"]
        assert doc.metadata["tags"] == ["motivation", "wisdom"]
        assert doc.metadata["url"] == f"{INSPIREME_URL}/quotes/quote-001"

    def test_quote_without_translations(self):
        quote = {
            "id": "quote-002",
            "content": "아는 것이 힘이다.",
            "author": "프랜시스 베이컨",
            "authorInfo": None,
            "translations": [],
            "topics": [],
            "tags": [],
        }
        doc = _build_quote_document(quote)

        assert '"아는 것이 힘이다."' in doc.page_content
        assert "— 프랜시스 베이컨" in doc.page_content
        assert "주제:" not in doc.page_content
        assert "태그:" not in doc.page_content
        assert "저자 소개:" not in doc.page_content
        assert "author_slug" not in doc.metadata

    def test_quote_without_author_info(self):
        quote = {
            "id": "quote-003",
            "content": "Test quote",
            "author": "Unknown Author",
            "translations": [],
        }
        doc = _build_quote_document(quote)

        assert doc.metadata["author"] == "Unknown Author"
        assert "author_slug" not in doc.metadata

    def test_url_format(self):
        quote = {
            "id": "abc-123-def",
            "content": "Test",
            "author": "Test",
        }
        doc = _build_quote_document(quote)
        assert doc.metadata["url"] == f"{INSPIREME_URL}/quotes/abc-123-def"


class TestBuildAuthorDocument:
    def test_author_with_ko_and_en(self):
        author_ko = {
            "id": "author-001",
            "slug": "albert-einstein",
            "name": "알베르트 아인슈타인",
            "nationality": "DE",
            "birthYear": 1879,
            "deathYear": 1955,
            "bio": "이론 물리학자",
        }
        author_en = {
            "id": "author-001",
            "slug": "albert-einstein",
            "name": "Albert Einstein",
            "bio": "Theoretical physicist",
        }
        doc = _build_author_document(author_ko, author_en)

        assert "알베르트 아인슈타인 (Albert Einstein)" in doc.page_content
        assert "국적: DE" in doc.page_content
        assert "출생: 1879, 사망: 1955" in doc.page_content
        assert "소개: 이론 물리학자" in doc.page_content
        assert "Bio: Theoretical physicist" in doc.page_content

        assert doc.metadata["blog_id"] == "inspireme"
        assert doc.metadata["type"] == "author"
        assert doc.metadata["author_id"] == "author-001"
        assert doc.metadata["author_slug"] == "albert-einstein"
        assert doc.metadata["url"] == f"{INSPIREME_URL}/authors/albert-einstein"

    def test_author_ko_only(self):
        author_ko = {
            "id": "author-002",
            "slug": "confucius",
            "name": "공자",
            "bio": "중국 철학자",
        }
        doc = _build_author_document(author_ko)

        assert "공자" in doc.page_content
        assert "(" not in doc.page_content  # no English name
        assert "소개: 중국 철학자" in doc.page_content
        assert "Bio:" not in doc.page_content

    def test_author_without_optional_fields(self):
        author_ko = {
            "id": "author-003",
            "slug": "",
            "name": "익명",
        }
        doc = _build_author_document(author_ko)

        assert doc.page_content == "익명"
        assert "국적:" not in doc.page_content
        assert "출생:" not in doc.page_content
        assert doc.metadata["author_slug"] == ""

    def test_author_birth_without_death(self):
        author_ko = {
            "id": "author-004",
            "slug": "living-author",
            "name": "현존 저자",
            "birthYear": 1980,
        }
        doc = _build_author_document(author_ko)

        assert "출생: 1980" in doc.page_content
        assert "사망:" not in doc.page_content


class TestInspiremeUrl:
    def test_points_to_real_domain(self):
        assert INSPIREME_URL == "https://inspire-me.advenoh.pe.kr"


class TestLoadInspiremeDocuments:
    """inspireme-be /api/* 는 X-Internal-Token 이 없으면 403 을 준다 (#44)."""

    def _install_fake_backend(self, monkeypatch, token, quote_total=1):
        seen = []
        quotes = [{"id": i, "content": f"명언{i}", "author": "저자"} for i in range(quote_total)]

        def handler(request: httpx.Request) -> httpx.Response:
            seen.append(request)
            if request.headers.get("X-Internal-Token") != token:
                return httpx.Response(403, json={"error": {"code": "FORBIDDEN"}})
            if request.url.path == "/api/quotes":
                # inspireme-be 는 {"quotes": [...], "total": N} 형태로 준다
                offset = int(request.url.params["offset"])
                limit = int(request.url.params["limit"])
                page = quotes[offset : offset + limit]
                return httpx.Response(200, json={"quotes": page, "total": len(quotes)})
            return httpx.Response(200, json={"authors": [], "total": 0})

        real_client = httpx.AsyncClient
        monkeypatch.setattr(
            inspireme_loader.httpx,
            "AsyncClient",
            lambda **kw: real_client(transport=httpx.MockTransport(handler), **kw),
        )
        return seen

    async def test_sends_internal_token_header(self, monkeypatch):
        seen = self._install_fake_backend(monkeypatch, token="secret")

        docs = await load_inspireme_documents("http://inspireme-be", internal_token="secret")

        assert len(docs) == 1
        assert seen and all(r.headers["X-Internal-Token"] == "secret" for r in seen)

    async def test_omits_header_when_token_empty(self, monkeypatch):
        seen = self._install_fake_backend(monkeypatch, token=None)

        await load_inspireme_documents("http://inspireme-be")

        assert seen and all("X-Internal-Token" not in r.headers for r in seen)

    async def test_paginates_quotes_by_total(self, monkeypatch):
        monkeypatch.setattr(inspireme_loader, "PAGE_SIZE", 2)
        seen = self._install_fake_backend(monkeypatch, token="t", quote_total=5)

        docs = await load_inspireme_documents("http://inspireme-be", internal_token="t")

        assert len(docs) == 5
        quote_calls = [r for r in seen if r.url.path == "/api/quotes"]
        assert len(quote_calls) == 3
