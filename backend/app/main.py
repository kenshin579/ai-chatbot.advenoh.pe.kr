from fastapi import FastAPI

app = FastAPI(
    title="RAG Chatbot API",
    description="RAG 기반 블로그 Q&A 챗봇 API 서버",
    version="0.1.0",
)


@app.get("/health")
async def health():
    return {"status": "ok"}
