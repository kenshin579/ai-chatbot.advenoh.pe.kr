"""Prometheus 지표 정의와 노출.

지표 이름과 라벨은 Go 백엔드(summora/moneyflow/inspireme)와 동일하게 맞춘다.
Grafana 대시보드가 `$app` 변수 하나로 네 앱을 모두 커버하기 때문이다.

app 라벨은 이 모듈이 붙이지 않는다. Prometheus 가 Pod 라벨 application 을
릴레이블해 주입한다.
"""

import os

from prometheus_client import (
    CONTENT_TYPE_LATEST,
    Counter,
    Gauge,
    Histogram,
    generate_latest,
)
from starlette.responses import Response

# 지표 노출 경로. Prometheus 의 kubernetes-pods job 에는 prometheus.io/path
# 릴레이블이 없어 metrics_path 가 /metrics 로 고정이다. 바꾸면 수집이 조용히 멈춘다.
METRICS_PATH = "/metrics"

# 컬렉터는 모듈 스코프에 한 번만 정의한다. 재임포트 시 중복 등록되면
# ValueError: Duplicated timeseries 가 발생한다.
#
# prometheus_client 는 Counter 이름에 "_total" 을 자동으로 붙인다. Go 서비스의
# 노출 이름을 그대로 맞추려면 "_total" 이 이미 붙은 이름을 넘기면 안 되고,
# "http_requests" 를 넘겨야 노출 시 "http_requests_total" 이 된다.
requests_total = Counter(
    "http_requests",
    "HTTP 요청 수",
    ["method", "route", "status"],
)

request_duration = Histogram(
    "http_request_duration_seconds",
    "HTTP 요청 처리 시간(초)",
    ["method", "route"],
    # Go 앱과 같은 버킷에 LLM 호출용 상한 30초를 더했다.
    buckets=(0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1, 2.5, 5, 10, 30),
)

build_info = Gauge(
    "app_build_info",
    "빌드 정보. 값은 항상 1이며 version/commit 을 라벨로 전달한다.",
    ["version", "commit"],
)

# 빌드 시 Dockerfile 의 ARG -> ENV 로 주입된다.
# 주입이 누락되면 dev 로 남아 대시보드 Version 컬럼에서 즉시 드러난다.
build_info.labels(
    version=os.getenv("APP_VERSION", "dev"),
    commit=os.getenv("APP_COMMIT", "unknown"),
).set(1)


def metrics_endpoint() -> Response:
    """Prometheus 노출 형식으로 지표를 반환한다."""
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)
