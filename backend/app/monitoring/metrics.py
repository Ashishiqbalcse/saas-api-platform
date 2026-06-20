from __future__ import annotations

import time

from prometheus_client import CONTENT_TYPE_LATEST, Counter, Gauge, Histogram, generate_latest
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

REQUESTS = Counter(
    "api_requests_total",
    "Total API requests.",
    ["method", "endpoint", "status_code", "plan"],
)
REQUEST_DURATION = Histogram(
    "api_request_duration_seconds",
    "API request latency in seconds.",
    ["method", "endpoint"],
    buckets=(0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1, 2.5, 5, 10),
)
RATE_LIMIT_HITS = Counter("api_rate_limit_hits_total", "Rate limit breaches.", ["plan"])
ACTIVE_TENANTS = Gauge("api_active_tenants", "Current active tenant count.")


def route_template(request: Request) -> str:
    route = request.scope.get("route")
    return getattr(route, "path", request.url.path)


def record_request(
    request: Request,
    status_code: int,
    plan: str = "anonymous",
    latency_s: float | None = None,
) -> None:
    endpoint = route_template(request)

    REQUESTS.labels(
        method=request.method,
        endpoint=endpoint,
        status_code=str(status_code),
        plan=plan,
  ).inc()
    if latency_s is not None:
        REQUEST_DURATION.labels(method=request.method, endpoint=endpoint).observe(latency_s)


class UsageMetricsMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        start = time.perf_counter()
        try:
            response = await call_next(request)
        except Exception:
            tenant = getattr(request.state, "tenant", None)
            record_request(
                request,
                status_code=500,
                plan=getattr(tenant, "plan", "anonymous"),
                latency_s=time.perf_counter() - start,
            )
            raise

        tenant = getattr(request.state, "tenant", None)
        record_request(
            request,
            status_code=response.status_code,
            plan=getattr(tenant, "plan", "anonymous"),
            latency_s=time.perf_counter() - start,
        )
        return response


def metrics_response() -> Response:
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)
