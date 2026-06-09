"""Tests for request-id propagation (T-03-03) and access logging (T-03-02)."""

from __future__ import annotations

import json
import logging
from uuid import UUID

from aimpos_config.logging import JsonFormatter, RequestIdFilter, request_id_var
from fastapi.testclient import TestClient

from app.dependencies import get_health_checks
from app.infrastructure.health.probes import DependencyStatus
from app.main import create_app

_ALL_OK = {name: DependencyStatus(status="ok") for name in ("postgresql", "redis", "minio")}


def _client() -> TestClient:
    app = create_app()
    app.dependency_overrides[get_health_checks] = lambda: _ALL_OK
    return TestClient(app)


def test_request_id_generated_and_returned() -> None:
    with _client() as client:
        response = client.get("/health")

    request_id = response.headers.get("X-Request-ID")
    assert request_id is not None
    # Generated ids are UUID4 strings.
    assert UUID(request_id).version == 4


def test_inbound_request_id_is_echoed() -> None:
    with _client() as client:
        response = client.get("/health", headers={"X-Request-ID": "trace-abc-123"})

    assert response.headers.get("X-Request-ID") == "trace-abc-123"


def test_each_request_gets_a_distinct_id() -> None:
    with _client() as client:
        first = client.get("/health").headers["X-Request-ID"]
        second = client.get("/health").headers["X-Request-ID"]

    assert first != second


def test_json_formatter_includes_request_id_and_extras() -> None:
    token = request_id_var.set("rid-123")
    try:
        record = logging.LogRecord(
            name="aimpos.access",
            level=logging.INFO,
            pathname=__file__,
            lineno=1,
            msg="http_request",
            args=None,
            exc_info=None,
        )
        record.status_code = 200
        RequestIdFilter().filter(record)
        rendered = JsonFormatter().format(record)
    finally:
        request_id_var.reset(token)

    payload = json.loads(rendered)
    assert payload["message"] == "http_request"
    assert payload["level"] == "INFO"
    assert payload["request_id"] == "rid-123"
    assert payload["status_code"] == 200


def test_access_log_line_correlates_with_request_id() -> None:
    class _Capture(logging.Handler):
        def __init__(self) -> None:
            super().__init__()
            self.records: list[logging.LogRecord] = []

        def emit(self, record: logging.LogRecord) -> None:
            self.records.append(record)

    capture = _Capture()
    capture.addFilter(RequestIdFilter())
    access_logger = logging.getLogger("aimpos.access")
    access_logger.addHandler(capture)
    access_logger.setLevel(logging.INFO)
    try:
        with _client() as client:
            response = client.get("/health")
    finally:
        access_logger.removeHandler(capture)

    assert len(capture.records) == 1
    record = capture.records[0]
    assert record.getMessage() == "http_request"
    assert record.http_method == "GET"  # type: ignore[attr-defined]
    assert record.path == "/health"  # type: ignore[attr-defined]
    assert record.status_code == 200  # type: ignore[attr-defined]
    assert record.request_id == response.headers["X-Request-ID"]  # type: ignore[attr-defined]
