import logging
import time

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

logger = logging.getLogger(__name__)


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        start = time.time()
        response = await call_next(request)
        latency_ms = int((time.time() - start) * 1000)

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
