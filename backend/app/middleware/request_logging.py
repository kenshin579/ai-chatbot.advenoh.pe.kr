import logging
import time

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

from app.metrics import METRICS_PATH, request_duration, requests_total

logger = logging.getLogger(__name__)


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # /metrics 자기 자신은 계측도 로깅도 하지 않는다.
        # 스크레이프마다 카운터가 늘어나면 요청량 그래프가 실제 트래픽이 아니라
        # 스크레이프 주기를 그리게 된다.
        if request.url.path == METRICS_PATH:
            return await call_next(request)

        start = time.time()
        perf_start = time.perf_counter()

        try:
            response = await call_next(request)
        except Exception:
            # ExceptionMiddleware 는 이 미들웨어보다 안쪽(APIRouter 쪽)에 있어
            # HTTPException 이 아닌 처리되지 않은 예외는 여기를 그대로 관통해
            # ServerErrorMiddleware 까지 올라간다. 감싸지 않으면 500 이 집계도
            # 로깅도 되지 않은 채 사라진다.
            route = request.scope.get("route")
            route_path = getattr(route, "path", None) or "unmatched"

            requests_total.labels(
                method=request.method,
                route=route_path,
                status="500",
            ).inc()
            request_duration.labels(
                method=request.method,
                route=route_path,
            ).observe(time.perf_counter() - perf_start)

            latency_ms = int((time.time() - start) * 1000)
            log_data = {
                "remoteIp": request.client.host if request.client else "",
                "host": request.headers.get("host", ""),
                "method": request.method,
                "uri": str(request.url.path),
                "status": 500,
                "latency": latency_ms,
                "latency_human": f"{latency_ms}ms",
                "userAgent": request.headers.get("user-agent", ""),
            }
            msg = f"{request.method} {request.url.path}"
            logger.error("[SERVER ERROR] %s", msg, extra=log_data)
            raise

        latency_ms = int((time.time() - start) * 1000)

        # 라우트 패턴은 call_next 이후에만 읽을 수 있다. BaseHTTPMiddleware 는
        # 라우팅 전에 실행되지만 scope 딕셔너리는 같은 객체가 그대로 전달돼
        # 라우터가 제자리에서 채운다. 매칭되지 않은 요청(404)에는 route 가 없다.
        route = request.scope.get("route")
        route_path = getattr(route, "path", None) or "unmatched"

        # 실제 URL(request.url.path)을 쓰면 경로 파라미터마다 시계열이 생겨
        # 카디널리티가 폭발한다. 반드시 라우트 패턴을 쓴다.
        requests_total.labels(
            method=request.method,
            route=route_path,
            status=str(response.status_code),
        ).inc()
        request_duration.labels(
            method=request.method,
            route=route_path,
        ).observe(time.perf_counter() - perf_start)

        log_data = {
            "remoteIp": request.client.host if request.client else "",
            "host": request.headers.get("host", ""),
            "method": request.method,
            "uri": str(request.url.path),
            "status": response.status_code,
            "latency": latency_ms,
            "latency_human": f"{latency_ms}ms",
            "userAgent": request.headers.get("user-agent", ""),
        }

        msg = f"{request.method} {request.url.path}"

        if response.status_code >= 500:
            logger.error("[SERVER ERROR] %s", msg, extra=log_data)
        elif response.status_code >= 400:
            logger.warning("[CLIENT ERROR] %s", msg, extra=log_data)
        else:
            logger.info("[RESPONSE] %s", msg, extra=log_data)

        return response
