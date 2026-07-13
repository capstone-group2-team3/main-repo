import json
import re
import time
import uuid
from collections import defaultdict
from datetime import datetime, timezone
from threading import Lock
from typing import Any

from starlette.responses import Response


REQUEST_ID_HEADER = "X-Request-ID"
PROMETHEUS_CONTENT_TYPE = "text/plain; version=0.0.4; charset=utf-8"
_REQUEST_ID_PATTERN = re.compile(r"^[A-Za-z0-9._:-]{1,128}$")


class MetricsRegistry:
    def __init__(self) -> None:
        self._lock = Lock()
        self.request_total: dict[tuple[str, str, str], int] = defaultdict(int)
        self.request_errors: dict[tuple[str, str], int] = defaultdict(int)
        self.request_latency_count: dict[tuple[str, str], int] = defaultdict(int)
        self.request_latency_sum: dict[tuple[str, str], float] = defaultdict(float)
        self.analyzed_cases_total = 0
        self.critical_overrides_total = 0
        self.retrieved_evidence_chunks_total = 0
        self.severity_predictions_total: dict[tuple[str, str], int] = defaultdict(int)

    def record_request(self, method: str, endpoint: str, status_code: int, latency_seconds: float) -> None:
        status_class = f"{status_code // 100}xx"
        key = (method, endpoint, status_class)
        latency_key = (method, endpoint)
        with self._lock:
            self.request_total[key] += 1
            self.request_latency_count[latency_key] += 1
            self.request_latency_sum[latency_key] += latency_seconds
            if status_code >= 500:
                self.request_errors[latency_key] += 1

    def record_analysis(self, result: dict[str, Any]) -> None:
        severity = result.get("severity") if isinstance(result.get("severity"), dict) else {}
        source = str(severity.get("source") or "unknown")
        label = str(severity.get("label") or "unknown")
        retrieved_sources = result.get("retrieved_sources", [])
        retrieved_count = len(retrieved_sources) if isinstance(retrieved_sources, list) else 0

        with self._lock:
            self.analyzed_cases_total += 1
            self.retrieved_evidence_chunks_total += retrieved_count
            self.severity_predictions_total[(source, label)] += 1
            if source == "critical_override":
                self.critical_overrides_total += 1

    def render_prometheus(self) -> str:
        with self._lock:
            request_total = dict(self.request_total)
            request_errors = dict(self.request_errors)
            latency_count = dict(self.request_latency_count)
            latency_sum = dict(self.request_latency_sum)
            severity_predictions = dict(self.severity_predictions_total)
            analyzed_cases_total = self.analyzed_cases_total
            critical_overrides_total = self.critical_overrides_total
            retrieved_evidence_chunks_total = self.retrieved_evidence_chunks_total

        lines = [
            "# HELP meddx_http_requests_total Total HTTP requests by method, endpoint, and status class.",
            "# TYPE meddx_http_requests_total counter",
        ]
        for (method, endpoint, status_class), value in sorted(request_total.items()):
            lines.append(
                f'meddx_http_requests_total{{method="{_esc(method)}",endpoint="{_esc(endpoint)}",status_class="{_esc(status_class)}"}} {value}'
            )

        lines.extend(
            [
                "# HELP meddx_http_request_errors_total Total HTTP 5xx responses by method and endpoint.",
                "# TYPE meddx_http_request_errors_total counter",
            ]
        )
        for (method, endpoint), value in sorted(request_errors.items()):
            lines.append(
                f'meddx_http_request_errors_total{{method="{_esc(method)}",endpoint="{_esc(endpoint)}"}} {value}'
            )

        lines.extend(
            [
                "# HELP meddx_http_request_latency_seconds Request latency summary by method and endpoint.",
                "# TYPE meddx_http_request_latency_seconds summary",
            ]
        )
        for (method, endpoint), value in sorted(latency_count.items()):
            labels = f'method="{_esc(method)}",endpoint="{_esc(endpoint)}"'
            lines.append(f"meddx_http_request_latency_seconds_count{{{labels}}} {value}")
            lines.append(f"meddx_http_request_latency_seconds_sum{{{labels}}} {latency_sum[(method, endpoint)]:.6f}")

        lines.extend(
            [
                "# HELP meddx_analyzed_cases_total Total report-analysis cases processed.",
                "# TYPE meddx_analyzed_cases_total counter",
                f"meddx_analyzed_cases_total {analyzed_cases_total}",
                "# HELP meddx_critical_overrides_total Total severity decisions forced by critical laboratory override.",
                "# TYPE meddx_critical_overrides_total counter",
                f"meddx_critical_overrides_total {critical_overrides_total}",
                "# HELP meddx_retrieved_evidence_chunks_total Total retrieved evidence chunks returned by report analysis.",
                "# TYPE meddx_retrieved_evidence_chunks_total counter",
                f"meddx_retrieved_evidence_chunks_total {retrieved_evidence_chunks_total}",
                "# HELP meddx_severity_predictions_total Severity predictions by source and label.",
                "# TYPE meddx_severity_predictions_total counter",
            ]
        )
        for (source, label), value in sorted(severity_predictions.items()):
            lines.append(
                f'meddx_severity_predictions_total{{source="{_esc(source)}",label="{_esc(label)}"}} {value}'
            )

        return "\n".join(lines) + "\n"


metrics_registry = MetricsRegistry()


class ObservabilityMiddleware:
    def __init__(self, app: Any) -> None:
        self.app = app

    async def __call__(self, scope: dict[str, Any], receive: Any, send: Any) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        request_id = _request_id(_header_value(scope.get("headers", []), REQUEST_ID_HEADER))
        scope.setdefault("state", {})["request_id"] = request_id
        started = time.perf_counter()
        status_code = 500

        async def send_wrapper(message: dict[str, Any]) -> None:
            nonlocal status_code
            if message["type"] == "http.response.start":
                status_code = int(message["status"])
                headers = list(message.get("headers", []))
                headers.append((REQUEST_ID_HEADER.lower().encode("latin-1"), request_id.encode("latin-1")))
                message = {**message, "headers": headers}
            await send(message)

        try:
            await self.app(scope, receive, send_wrapper)
        except Exception:
            status_code = 500
            raise
        finally:
            latency_seconds = time.perf_counter() - started
            endpoint = _route_path(scope)
            metrics_registry.record_request(
                method=scope["method"],
                endpoint=endpoint,
                status_code=status_code,
                latency_seconds=latency_seconds,
            )
            _write_request_log(
                request_id=request_id,
                method=scope["method"],
                endpoint=endpoint,
                status_code=status_code,
                latency_seconds=latency_seconds,
            )


def metrics_response() -> Response:
    return Response(
        content=metrics_registry.render_prometheus(),
        media_type=PROMETHEUS_CONTENT_TYPE,
    )


def _request_id(value: str | None) -> str:
    if value and _REQUEST_ID_PATTERN.fullmatch(value):
        return value
    return str(uuid.uuid4())


def _header_value(headers: list[tuple[bytes, bytes]], name: str) -> str | None:
    expected = name.lower().encode("latin-1")
    for key, value in headers:
        if key.lower() == expected:
            return value.decode("latin-1")
    return None


def _route_path(scope: dict[str, Any]) -> str:
    route = scope.get("route")
    path = getattr(route, "path", None)
    return str(path or scope.get("path") or "unknown")


def _write_request_log(
    request_id: str,
    method: str,
    endpoint: str,
    status_code: int,
    latency_seconds: float,
) -> None:
    print(
        json.dumps(
            {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "level": "INFO" if status_code < 500 else "ERROR",
                "request_id": request_id,
                "method": method,
                "endpoint": endpoint,
                "status_code": status_code,
                "latency_ms": round(latency_seconds * 1000, 3),
            },
            separators=(",", ":"),
        ),
        flush=True,
    )


def _esc(value: str) -> str:
    return value.replace("\\", "\\\\").replace("\n", "\\n").replace('"', '\\"')
