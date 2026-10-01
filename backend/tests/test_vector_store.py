from langchain_core.documents import Document

from app.rag import vector_store
from app.rag.vector_store import VectorStoreManager


class _RecordingStore:
    def __init__(self):
        self.calls = []

    def add_documents(self, documents):
        self.calls.append(len(documents))


class TestIndexDocuments:
    """문서 전체를 한 번에 넣으면 ChromaDB 가 OOMKilled 된다 (#46)."""

    def _manager(self, monkeypatch):
        store = _RecordingStore()
        manager = VectorStoreManager("localhost", 8000, embeddings=None)
        monkeypatch.setattr(manager, "get_store", lambda blog_id: store)
        return manager, store

    def test_adds_in_batches(self, monkeypatch):
        monkeypatch.setattr(vector_store, "INDEX_BATCH_SIZE", 2)
        manager, store = self._manager(monkeypatch)
        docs = [Document(page_content=str(i)) for i in range(5)]

        indexed = manager.index_documents("inspireme", docs)

        assert indexed == 5
        assert store.calls == [2, 2, 1]

    def test_empty_documents_makes_no_call(self, monkeypatch):
        manager, store = self._manager(monkeypatch)

        assert manager.index_documents("inspireme", []) == 0
        assert store.calls == []
