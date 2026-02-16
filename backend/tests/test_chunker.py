from langchain_core.documents import Document

from app.rag.chunker import create_text_splitter, split_documents


class TestCreateTextSplitter:
    def test_default_parameters(self):
        splitter = create_text_splitter()
        assert splitter._chunk_size == 1000
        assert splitter._chunk_overlap == 200

    def test_custom_parameters(self):
        splitter = create_text_splitter(chunk_size=500, chunk_overlap=100)
        assert splitter._chunk_size == 500
        assert splitter._chunk_overlap == 100

    def test_markdown_separators(self):
        splitter = create_text_splitter()
        assert "\n## " in splitter._separators
        assert "\n### " in splitter._separators


class TestSplitDocuments:
    def test_short_document_not_split(self):
        doc = Document(
            page_content="짧은 문서입니다.",
            metadata={"title": "테스트", "blog_id": "blog-v2"},
        )
        chunks = split_documents([doc], chunk_size=1000, chunk_overlap=200)
        assert len(chunks) == 1
        assert chunks[0].metadata["title"] == "테스트"
        assert chunks[0].metadata["blog_id"] == "blog-v2"

    def test_long_document_split(self):
        long_content = "\n\n".join([f"단락 {i}: " + "내용 " * 50 for i in range(20)])
        doc = Document(
            page_content=long_content,
            metadata={"title": "긴 문서", "blog_id": "blog-v2"},
        )
        chunks = split_documents([doc], chunk_size=500, chunk_overlap=100)
        assert len(chunks) > 1
        # 모든 청크에 원본 metadata가 보존되는지 확인
        for chunk in chunks:
            assert chunk.metadata["title"] == "긴 문서"
            assert chunk.metadata["blog_id"] == "blog-v2"

    def test_heading_based_split(self):
        content = (
            "# 제목\n\n소개 내용입니다.\n\n"
            "## 섹션 1\n\n" + "첫 번째 섹션 내용. " * 100 + "\n\n"
            "## 섹션 2\n\n" + "두 번째 섹션 내용. " * 100 + "\n\n"
            "## 섹션 3\n\n" + "세 번째 섹션 내용. " * 100
        )
        doc = Document(page_content=content, metadata={"title": "헤딩 테스트"})
        chunks = split_documents([doc], chunk_size=500, chunk_overlap=50)
        assert len(chunks) > 1

    def test_empty_document(self):
        doc = Document(page_content="", metadata={"title": "빈 문서"})
        chunks = split_documents([doc], chunk_size=1000, chunk_overlap=200)
        assert len(chunks) == 0

    def test_metadata_preserved_across_chunks(self):
        content = "내용 " * 500
        metadata = {
            "title": "메타데이터 보존 테스트",
            "blog_id": "blog-v2",
            "category": "go",
            "tags": ["go", "golang"],
            "url": "https://blog-v2.advenoh.pe.kr/test-post",
        }
        doc = Document(page_content=content, metadata=metadata)
        chunks = split_documents([doc], chunk_size=200, chunk_overlap=50)
        assert len(chunks) > 1
        for chunk in chunks:
            assert chunk.metadata["title"] == "메타데이터 보존 테스트"
            assert chunk.metadata["blog_id"] == "blog-v2"
            assert chunk.metadata["category"] == "go"
            assert chunk.metadata["tags"] == ["go", "golang"]
