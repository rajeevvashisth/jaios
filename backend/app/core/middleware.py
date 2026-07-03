import time
import uuid

import structlog
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response

from app.core.logging import get_logger
from app.core.metrics import http_request_duration_seconds, http_requests_total

logger = get_logger(__name__)


def _path_template(request: Request) -> str:
    """Prefer the matched route's path template (``/tasks/{task_id}``) over
    the raw URL (``/tasks/abc-123``) so per-path metrics don't explode into
    one series per unique ID."""
    route = request.scope.get("route")
    if route is not None and hasattr(route, "path"):
        return str(route.path)
    return request.url.path


class ObservabilityMiddleware(BaseHTTPMiddleware):
    """Assigns a request ID (returned as ``X-Request-ID`` and bound into
    every log line for the request's duration), and records request count +
    latency metrics per method/path-template/status."""

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
        start = time.perf_counter()

        structlog.contextvars.clear_contextvars()
        structlog.contextvars.bind_contextvars(request_id=request_id)

        response = await call_next(request)

        duration = time.perf_counter() - start
        path = _path_template(request)

        http_requests_total.labels(
            method=request.method, path=path, status=str(response.status_code)
        ).inc()
        http_request_duration_seconds.labels(method=request.method, path=path).observe(duration)

        logger.info(
            "http_request",
            method=request.method,
            path=path,
            status=response.status_code,
            duration_ms=round(duration * 1000, 2),
        )

        response.headers["X-Request-ID"] = request_id
        return response
