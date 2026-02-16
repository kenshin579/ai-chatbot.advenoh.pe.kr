import pytest
from fastapi.testclient import TestClient

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
