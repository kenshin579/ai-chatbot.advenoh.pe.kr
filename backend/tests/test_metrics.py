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
        # 스크레이프마다 카운터가 늘어나면 요청량 그래프가
        # 실제 트래픽이 아니라 스크레이프 주기를 그리게 된다.
        body = client.get("/metrics").text

        assert 'route="/metrics"' not in body
