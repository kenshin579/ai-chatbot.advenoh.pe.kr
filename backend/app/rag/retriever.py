from langchain_chroma import Chroma
from langchain_classic.retrievers import MergerRetriever
from langchain_community.retrievers import BM25Retriever
from langchain_core.documents import Document
from langchain_core.retrievers import RetrieverLike


def create_retriever(vector_store: Chroma, top_k: int = 5) -> RetrieverLike:
    """벡터 저장소에서 유사도 기반 검색기를 생성한다."""
    return vector_store.as_retriever(search_kwargs={"k": top_k})


def create_hybrid_retriever(
    vector_store: Chroma,
    documents: list[Document],
    top_k: int = 5,
) -> RetrieverLike:
    """Hybrid Search 검색기를 생성한다 (BM25 키워드 + 시맨틱 벡터 검색).

    MergerRetriever로 두 검색기 결과를 병합한다.
    """
    # 시맨틱 검색기
    semantic_retriever = vector_store.as_retriever(search_kwargs={"k": top_k})

    # BM25 키워드 검색기
    bm25_retriever = BM25Retriever.from_documents(documents, k=top_k)

    # 두 검색기 결과 병합
    return MergerRetriever(retrievers=[semantic_retriever, bm25_retriever])
