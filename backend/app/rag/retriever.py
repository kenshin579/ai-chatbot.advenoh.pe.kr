from langchain_chroma import Chroma
from langchain_core.retrievers import RetrieverLike


def create_retriever(vector_store: Chroma, top_k: int = 5) -> RetrieverLike:
    """벡터 저장소에서 유사도 기반 검색기를 생성한다."""
    return vector_store.as_retriever(search_kwargs={"k": top_k})
