from langchain_classic.chains import create_history_aware_retriever, create_retrieval_chain
from langchain_classic.chains.combine_documents import create_stuff_documents_chain
from langchain_chroma import Chroma
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_openai import ChatOpenAI

from app.prompts.templates import SYSTEM_PROMPT


def create_rag_chain(vector_store: Chroma, model: str, top_k: int = 5):
    """대화 히스토리를 지원하는 RAG 체인을 생성한다."""
    llm = ChatOpenAI(model=model, temperature=0)
    retriever = vector_store.as_retriever(search_kwargs={"k": top_k})

    # 대화 히스토리를 고려한 질문 재작성 체인
    contextualize_prompt = ChatPromptTemplate.from_messages([
        ("system", "대화 히스토리와 최신 사용자 질문을 고려하여, "
         "대화 히스토리 없이도 이해할 수 있는 독립적인 질문으로 재작성하세요. "
         "질문을 답변하지 마세요. 재작성이 필요 없으면 그대로 반환하세요."),
        MessagesPlaceholder("chat_history"),
        ("human", "{input}"),
    ])
    history_aware_retriever = create_history_aware_retriever(
        llm, retriever, contextualize_prompt
    )

    # QA 체인
    qa_prompt = ChatPromptTemplate.from_messages([
        ("system", SYSTEM_PROMPT),
        MessagesPlaceholder("chat_history"),
        ("human", "{input}"),
    ])
    question_answer_chain = create_stuff_documents_chain(llm, qa_prompt)

    return create_retrieval_chain(history_aware_retriever, question_answer_chain)
