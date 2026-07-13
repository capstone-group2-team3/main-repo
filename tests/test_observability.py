import json

import anyio
from starlette.responses import JSONResponse

from app.api import routes as api_routes
from app.services.observability import ObservabilityMiddleware, metrics_response


async def _inner_observability_app(scope, receive, send):
    response = metrics_response() if scope["path"] == "/metrics" else JSONResponse({"status": "ok"})
    await response(scope, receive, send)


def _asgi_get(app, path: str, headers: dict[str, str] | None = None):
    async def call():
        messages = []
        request_sent = False
        scope = {
            "type": "http",
            "asgi": {"version": "3.0"},
            "http_version": "1.1",
            "method": "GET",
            "scheme": "http",
            "path": path,
            "raw_path": path.encode("ascii"),
            "query_string": b"",
            "headers": [
                (key.lower().encode("latin-1"), value.encode("latin-1"))
                for key, value in (headers or {}).items()
            ],
            "client": ("testclient", 50000),
            "server": ("testserver", 80),
        }

        async def receive():
            nonlocal request_sent
            if not request_sent:
                request_sent = True
                return {"type": "http.request", "body": b"", "more_body": False}
            await anyio.sleep(0)
            return {"type": "http.disconnect"}

        async def send(message):
            messages.append(message)

        await app(scope, receive, send)
        start = next(message for message in messages if message["type"] == "http.response.start")
        body = b"".join(message.get("body", b"") for message in messages if message["type"] == "http.response.body")
        return {
            "status_code": start["status"],
            "headers": {key.decode("latin-1"): value.decode("latin-1") for key, value in start["headers"]},
            "text": body.decode("utf-8"),
        }

    return anyio.run(call)


def test_metrics_endpoint_exposes_prometheus_metrics():
    app = ObservabilityMiddleware(_inner_observability_app)
    _asgi_get(app, "/health")
    response = _asgi_get(app, "/metrics")

    assert response["status_code"] == 200
    assert response["headers"]["content-type"].startswith("text/plain")
    body = response["text"]
    assert "meddx_http_requests_total" in body
    assert "meddx_http_request_latency_seconds_count" in body
    assert "meddx_http_request_errors_total" in body
    assert "meddx_analyzed_cases_total" in body


def test_request_id_header_is_reused_and_logged_as_json(capsys):
    request_id = "capstone-audit-request-1"

    response = _asgi_get(
        ObservabilityMiddleware(_inner_observability_app),
        "/health",
        headers={"X-Request-ID": request_id},
    )

    assert response["status_code"] == 200
    assert response["headers"]["x-request-id"] == request_id

    captured = capsys.readouterr().out.splitlines()
    request_logs = [
        json.loads(line)
        for line in captured
        if line.startswith("{") and f'"request_id":"{request_id}"' in line
    ]

    assert request_logs
    log = request_logs[-1]
    assert log["request_id"] == request_id
    assert log["method"] == "GET"
    assert log["endpoint"] == "/health"
    assert log["status_code"] == 200
    assert isinstance(log["latency_ms"], float)
    assert "symptoms" not in log
    assert "laboratory" not in log


def test_api_metrics_route_returns_prometheus_response():
    response = api_routes.metrics()

    assert response.status_code == 200
    assert response.media_type.startswith("text/plain")
