import chromadb
from langchain_chroma import Chroma
from langchain_core.documents import Document
from langchain_openai import OpenAIEmbeddings


class VectorStoreManager:
    """ChromaDB 기반 벡터 저장소 관리자. blog_id별 Collection을 분리 관리한다."""

    def __init__(self, host: str, port: int, embeddings: OpenAIEmbeddings):
        self.client = chromadb.HttpClient(host=host, port=port)
        self.embeddings = embeddings

    def get_store(self, blog_id: str) -> Chroma:
        """blog_id에 해당하는 Collection을 Chroma wrapper로 반환한다."""
        return Chroma(
            client=self.client,
            collection_name=blog_id,
            embedding_function=self.embeddings,
        )

    def index_documents(self, blog_id: str, documents: list[Document]) -> int:
        """문서를 해당 Collection에 인덱싱한다. 인덱싱된 청크 수를 반환한다."""
        store = self.get_store(blog_id)
        store.add_documents(documents)
        return len(documents)

    def delete_collection(self, blog_id: str) -> None:
        """Collection을 삭제한다 (재인덱싱 시 사용)."""
        try:
            self.client.delete_collection(name=blog_id)
        except Exception:
            pass  # Collection이 없으면 무시

    def list_collections(self) -> list[str]:
        """사용 가능한 Collection 목록을 반환한다."""
        collections = self.client.list_collections()
        return [c.name for c in collections]
