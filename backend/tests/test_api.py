import asyncio
import time

import httpx
import pytest
from fastapi.testclient import TestClient

from app.api import routes
from app.api.routes import get_vector_store_manager, verify_index_token
from app.main import app


@pytest.fixture
def client():
    return TestClient(app)


class TestHealthEndpoint:
    def test_health_returns_ok(self, client):
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json() == {"status": "ok"}


class TestChatEndpoint:
    def test_invalid_blog_id_returns_400(self, client):
        response = client.post(
            "/chat",
            json={
                "blog_id": "invalid-blog",
                "question": "테스트 질문",
            },
        )
        assert response.status_code == 400
        assert "Unknown blog_id" in response.json()["detail"]

    def test_missing_question_returns_422(self, client):
        response = client.post(
            "/chat",
            json={"blog_id": "blog-v2"},
        )
        assert response.status_code == 422


class TestIndexEndpoint:
    def test_no_auth_returns_401(self, client):
        response = client.post("/index/blog-v2")
        assert response.status_code == 401

    def test_invalid_token_returns_401(self, client):
        response = client.post(
            "/index/blog-v2",
            headers={"Authorization": "Bearer wrong-token"},
        )
        assert response.status_code in (401, 500)  # 500 if token not configured


class _SlowManager:
    """동기 호출이 오래 걸리는 VectorStoreManager 대역."""

    def __init__(self, block_seconds: float):
        self.block_seconds = block_seconds

    def delete_collection(self, blog_id):
        time.sleep(self.block_seconds)

    def index_documents(self, blog_id, documents):
        time.sleep(self.block_seconds)
        return len(documents)


class TestIndexDoesNotBlockEventLoop:
    """재인덱싱 중에도 /health 가 응답해야 liveness 에 죽지 않는다 (#42)."""

    async def test_health_responds_during_reindex(self, monkeypatch):
        block = 1.0

        async def fake_load(_url):
            return []

        monkeypatch.setattr(routes, "load_inspireme_documents", fake_load)
        app.dependency_overrides[get_vector_store_manager] = lambda: _SlowManager(block)
        app.dependency_overrides[verify_index_token] = lambda: "token"
        try:
            transport = httpx.ASGITransport(app=app)
            async with httpx.AsyncClient(transport=transport, base_url="http://test") as ac:
                # 기준 시각은 reindex 전에 잡는다. 루프가 막히면 아래 sleep 자체가
                # 늦게 깨어나므로, sleep 뒤에 재면 막힌 구간을 놓친다.
                start = time.monotonic()
                reindex = asyncio.create_task(ac.post("/index/inspireme"))
                await asyncio.sleep(0.1)  # 핸들러가 동기 작업에 들어가게 한다

                health = await ac.get("/health")
                elapsed = time.monotonic() - start

                resp = await reindex
        finally:
            app.dependency_overrides.clear()

        assert health.status_code == 200
        assert elapsed < block / 2
        assert resp.status_code == 200
        assert resp.json()["indexed_chunks"] == 0
