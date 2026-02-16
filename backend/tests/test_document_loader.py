import tempfile
from pathlib import Path

from app.rag.document_loader import build_post_url, load_blog_documents, parse_frontmatter


class TestParseFrontmatter:
    def test_valid_frontmatter(self):
        content = '---\ntitle: "테스트 제목"\ndate: 2024-01-15\ntags:\n  - go\n  - golang\n---\n\n본문 내용입니다.'
        metadata, body = parse_frontmatter(content)
        assert metadata["title"] == "테스트 제목"
        assert metadata["tags"] == ["go", "golang"]
        assert "본문 내용입니다." in body

    def test_no_frontmatter(self):
        content = "프론트매터 없는 문서입니다."
        metadata, body = parse_frontmatter(content)
        assert metadata == {}
        assert body == content

    def test_empty_frontmatter(self):
        content = "---\n---\n\n본문"
        metadata, body = parse_frontmatter(content)
        assert metadata == {}
        assert "본문" in body


class TestBuildPostUrl:
    def test_blog_v2_url(self):
        url = build_post_url("go/go에서의-열거형-상수-enums-in-go/index.md", "blog-v2")
        assert url == "https://blog-v2.advenoh.pe.kr/go에서의-열거형-상수-enums-in-go"

    def test_investment_url(self):
        url = build_post_url("investing/투자-인사이트/index.md", "investment")
        assert url == "https://investment.advenoh.pe.kr/투자-인사이트"

    def test_unknown_blog_id(self):
        url = build_post_url("go/test-post/index.md", "unknown")
        assert url == "/test-post"


class TestLoadBlogDocuments:
    def test_load_from_temp_dir(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            # 블로그 글 디렉토리 구조 생성
            post_dir = Path(tmpdir) / "go" / "test-post"
            post_dir.mkdir(parents=True)
            md_file = post_dir / "index.md"
            md_file.write_text(
                '---\ntitle: "테스트 포스트"\ndate: 2024-01-15\ntags:\n  - go\n---\n\n'
                "# 테스트\n\n본문 내용입니다.",
                encoding="utf-8",
            )

            docs = load_blog_documents(tmpdir, "blog-v2")
            assert len(docs) == 1
            assert docs[0].metadata["title"] == "테스트 포스트"
            assert docs[0].metadata["blog_id"] == "blog-v2"
            assert docs[0].metadata["category"] == "go"
            assert "본문 내용입니다." in docs[0].page_content

    def test_load_nonexistent_dir(self):
        try:
            load_blog_documents("/nonexistent/path", "blog-v2")
            assert False, "Should raise FileNotFoundError"
        except FileNotFoundError:
            pass

    def test_load_multiple_posts(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            for i in range(3):
                post_dir = Path(tmpdir) / "go" / f"post-{i}"
                post_dir.mkdir(parents=True)
                (post_dir / "index.md").write_text(
                    f'---\ntitle: "포스트 {i}"\n---\n\n내용 {i}',
                    encoding="utf-8",
                )

            docs = load_blog_documents(tmpdir, "blog-v2")
            assert len(docs) == 3
