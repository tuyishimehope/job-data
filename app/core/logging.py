from datetime import datetime, timezone
import json
import logging
from app.core.settings import settings
from app.core.context import request_id_context


class JSONFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:

        log_data = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "service": settings.app_name,
            "environment": settings.environment}
        request_id = request_id_context.get()

        if request_id is not None:
            log_data["request_id"] = request_id

        custom_fields = [
            "event",
            "company",
            "job_id",
            "job_title",
            "total",
            "status_code",
            "http_method",
            "http_path",
            "duration_ms"
        ]

        for field in custom_fields:
            value = getattr(record, field, None)

            if value is not None:
                log_data[field] = value

        if record.exc_info:
            log_data["exception"] = self.formatException(
                record.exc_info
            )

        return json.dumps(log_data)


def configure_logging() -> None:
    handler = logging.StreamHandler()
    handler.setFormatter(JSONFormatter())

    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)

    root_logger.handlers.clear()
    root_logger.addHandler(handler)
