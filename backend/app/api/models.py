from pydantic import BaseModel


class ChatMessage(BaseModel):
    role: str  # "human" | "ai"
    content: str


class ChatRequest(BaseModel):
    blog_id: str
    question: str
    chat_history: list[ChatMessage] | None = None


class Source(BaseModel):
    title: str
    url: str


class ChatResponse(BaseModel):
    answer: str
    sources: list[Source]
    message_id: str = ""


class IndexResponse(BaseModel):
    status: str
    blog_id: str
    indexed_chunks: int


class HealthResponse(BaseModel):
    status: str
