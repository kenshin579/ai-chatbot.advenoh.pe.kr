"""메트릭 노출 테스트.

주의: prometheus_client 의 기본 레지스트리는 프로세스 전역이라
카운터가 테스트 간에 누적된다. 정확한 값을 단언하지 않는다.
"""

import sys

import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture
def client():
    return TestClient(app)


class TestMetricsEndpoint:
    def test_metrics_exposes_build_info(self, client):
        response = client.get("/metrics")

        assert response.status_code == 200
        assert "app_build_info" in response.text

    @pytest.mark.skipif(
        not sys.platform.startswith("linux"),
        reason="prometheus_client 의 ProcessCollector 는 /proc 을 읽으므로 리눅스에서만 동작한다",
    )
    def test_metrics_exposes_process_start_time(self, client):
        # 대시보드 배포 마커 판정 기준이라 컨테이너(리눅스)에서는 반드시 있어야 한다.
        # macOS 개발 머신에서는 나오지 않는 것이 정상이므로 건너뛴다.
        response = client.get("/metrics")

        assert "process_start_time_seconds" in response.text

    def test_records_request_with_route_pattern(self, client):
        # 실제 URL 이 아니라 라우트 패턴이 route 라벨로 기록돼야 한다.
        # 실제 URL 을 쓰면 blog_id 마다 시계열이 생겨 카디널리티가 폭발한다.
        client.post("/index/blog-v2")
        client.post("/index/investment")

        body = client.get("/metrics").text

        assert 'route="/index/{blog_id}"' in body
        assert 'route="/index/blog-v2"' not in body

    def test_records_health_request(self, client):
        client.get("/health")

        body = client.get("/metrics").text

        assert 'route="/health"' in body

    def test_metrics_endpoint_does_not_record_itself(self, client):
        # 한 번만 긁으면 카운터 증가가 응답 생성 이후라 구조적으로 자기 자신을
        # 볼 수 없어, 제외 로직을 지워도 이 테스트가 통과한다. 두 번 긁는다.
        client.get("/metrics")
        body = client.get("/metrics").text

        assert 'route="/metrics"' not in body

    def test_records_unhandled_exception_as_500(self, client):
        # ExceptionMiddleware 는 이 미들웨어보다 안쪽이라 HTTPException 이 아닌
        # 처리되지 않은 예외가 관통해 나간다. 감싸주지 않으면 실제 500 이
        # 대시보드에서 사라진다.
        from app.main import app as fastapi_app

        @fastapi_app.get("/__metrics_boom", include_in_schema=False)
        async def _boom():
            raise RuntimeError("boom")

        probe = TestClient(fastapi_app, raise_server_exceptions=False)
        assert probe.get("/__metrics_boom").status_code == 500

        body = probe.get("/metrics").text

        assert 'route="/__metrics_boom"' in body
        assert 'status="500"' in body
