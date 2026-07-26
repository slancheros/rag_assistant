import json
import logging
import logging.config
from contextvars import ContextVar, Token
from datetime import datetime, timezone
from typing import Any


request_id_context: ContextVar[str | None] = ContextVar(
    "request_id",
    default=None,
)

STANDARD_LOG_RECORD_FIELDS = frozenset(
    logging.makeLogRecord({}).__dict__
)


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, Any] = {
            "timestamp": datetime.fromtimestamp(
                record.created,
                tz=timezone.utc,
            ).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "event": record.getMessage(),
        }

        request_id = request_id_context.get()
        if request_id:
            payload["request_id"] = request_id

        for key, value in record.__dict__.items():
            if (
                key not in STANDARD_LOG_RECORD_FIELDS
                and not key.startswith("_")
            ):
                payload[key] = value

        if record.exc_info:
            payload["exception"] = self.formatException(
                record.exc_info
            )

        return json.dumps(
            payload,
            default=str,
            separators=(",", ":"),
        )


def configure_logging(level: str = "INFO") -> None:
    normalized_level = level.upper()

    logging.config.dictConfig(
        {
            "version": 1,
            "disable_existing_loggers": False,
            "formatters": {
                "json": {
                    "()": JsonFormatter,
                }
            },
            "handlers": {
                "default": {
                    "class": "logging.StreamHandler",
                    "formatter": "json",
                    "stream": "ext://sys.stdout",
                }
            },
            "root": {
                "handlers": ["default"],
                "level": normalized_level,
            },
            "loggers": {
                "uvicorn.access": {
                    "handlers": [],
                    "propagate": False,
                },
            },
        }
    )


def bind_request_id(request_id: str) -> Token[str | None]:
    return request_id_context.set(request_id)


def reset_request_id(token: Token[str | None]) -> None:
    request_id_context.reset(token)
