import json
import logging
import logging.handlers
import os
from datetime import datetime, timezone

LOG_DIR = "logs"
ERROR_LOG_FILE = os.path.join(LOG_DIR, "errors.jsonl")

# Fields pulled from record.__dict__ via logger.*(... extra=...)
_EXTRA_FIELDS = ("input_text", "user_id", "error_type", "stage")


class JsonFormatter(logging.Formatter):
    """Format a LogRecord as a single JSON object per line."""

    def format(self, record):
        payload = {
            "time": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }

        for field in _EXTRA_FIELDS:
            if field in record.__dict__:
                payload[field] = record.__dict__[field]

        if record.exc_info:
            payload["traceback"] = self.formatException(record.exc_info)
            if "error_type" not in payload:
                payload["error_type"] = record.exc_info[0].__name__

        return json.dumps(payload, ensure_ascii=False)


def setup_logging():
    """Configure root logger with stdout (INFO) and JSONL file (ERROR) handlers."""
    os.makedirs(LOG_DIR, exist_ok=True)

    root = logging.getLogger()
    root.setLevel(logging.INFO)

    # Avoid duplicate handlers if setup_logging is called more than once
    root.handlers.clear()

    stream_handler = logging.StreamHandler()
    stream_handler.setLevel(logging.INFO)
    stream_handler.setFormatter(
        logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    )
    root.addHandler(stream_handler)

    file_handler = logging.handlers.TimedRotatingFileHandler(
        ERROR_LOG_FILE,
        when="midnight",
        backupCount=30,
        encoding="utf-8",
        utc=True,
    )
    file_handler.setLevel(logging.ERROR)
    file_handler.setFormatter(JsonFormatter())
    root.addHandler(file_handler)
