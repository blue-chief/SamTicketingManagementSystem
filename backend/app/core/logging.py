"""Structured JSON logging – no message bodies or personal data (rule 5)."""

import json
import logging
import sys
from datetime import UTC, datetime


class JSONFormatter(logging.Formatter):
    """Emit one JSON object per log line."""

    REDACT_FIELDS = {"body", "body_text", "password", "secret", "token", "ocr_text"}

    def format(self, record: logging.LogRecord) -> str:
        log_entry: dict = {
            "timestamp": datetime.now(UTC).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        if record.exc_info and record.exc_info[0] is not None:
            log_entry["exception"] = self.formatException(record.exc_info)
        # Strip any extra fields that are PII
        if hasattr(record, "extra"):
            safe = {
                k: v
                for k, v in record.extra.items()  # type: ignore[attr-defined]
                if k.lower() not in self.REDACT_FIELDS
            }
            log_entry["extra"] = safe
        return json.dumps(log_entry, default=str)


def setup_logging() -> None:
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JSONFormatter())
    root = logging.getLogger()
    root.handlers.clear()
    root.addHandler(handler)
    root.setLevel(logging.INFO)
    # Silence noisy libraries
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
