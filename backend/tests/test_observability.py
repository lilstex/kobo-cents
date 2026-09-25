import json
import logging

from fastapi.testclient import TestClient

from app.core.logging import JsonFormatter, request_id_var
from app.main import app

client = TestClient(app)


def test_health_response_carries_a_request_id_header():
    response = client.get("/health")
    assert "x-request-id" in response.headers
    assert len(response.headers["x-request-id"]) > 0


def test_a_request_id_sent_in_is_echoed_back():
    response = client.get("/health", headers={"x-request-id": "test-fixed-id"})
    assert response.headers["x-request-id"] == "test-fixed-id"


def test_json_formatter_produces_valid_json_with_the_current_request_id():
    token = request_id_var.set("abc123")
    try:
        record = logging.LogRecord(
            name="app",
            level=logging.INFO,
            pathname=__file__,
            lineno=1,
            msg="hello",
            args=(),
            exc_info=None,
        )
        formatted = JsonFormatter().format(record)
    finally:
        request_id_var.reset(token)

    payload = json.loads(formatted)
    assert payload["message"] == "hello"
    assert payload["request_id"] == "abc123"
    assert payload["level"] == "INFO"
