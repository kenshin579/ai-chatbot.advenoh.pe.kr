from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter


def create_text_splitter(
    chunk_size: int = 1000,
    chunk_overlap: int = 200,
) -> RecursiveCharacterTextSplitter:
    """마크다운에 적합한 텍스트 스플리터를 생성한다."""
    return RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        separators=[
            "\n## ",   # H2
            "\n### ",  # H3
            "\n#### ", # H4
            "\n\n",    # 빈 줄
            "\n",      # 줄바꿈
            " ",       # 공백
        ],
        length_function=len,
    )


def split_documents(
    documents: list[Document],
    chunk_size: int = 1000,
    chunk_overlap: int = 200,
) -> list[Document]:
    """문서를 청크로 분할한다. 각 청크에 원본 metadata가 보존된다."""
    splitter = create_text_splitter(chunk_size, chunk_overlap)
    return splitter.split_documents(documents)
