from langchain_openai import OpenAIEmbeddings


def create_embeddings(model: str = "text-embedding-3-small") -> OpenAIEmbeddings:
    """OpenAI 임베딩 모델을 생성한다."""
    return OpenAIEmbeddings(model=model)
