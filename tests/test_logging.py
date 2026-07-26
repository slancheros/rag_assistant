import json
import logging

from app.core.logging import (
    JsonFormatter,
    bind_request_id,
    reset_request_id,
)


def test_json_formatter_includes_context_and_fields() -> None:
    formatter = JsonFormatter()
    record = logging.LogRecord(
        name="app.test",
        level=logging.INFO,
        pathname=__file__,
        lineno=1,
        msg="retrieval_completed",
        args=(),
        exc_info=None,
    )
    record.top_k = 3
    token = bind_request_id("request-123")

    try:
        payload = json.loads(formatter.format(record))
    finally:
        reset_request_id(token)

    assert payload["event"] == "retrieval_completed"
    assert payload["level"] == "INFO"
    assert payload["request_id"] == "request-123"
    assert payload["top_k"] == 3
