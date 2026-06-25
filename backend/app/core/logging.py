import logging
import os
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path

from pythonjsonlogger.json import JsonFormatter

from app.core.config import get_settings


def setup_logging() -> None:
    settings = get_settings()

    log_dir = Path(settings.log_dir)
    log_dir.mkdir(parents=True, exist_ok=True)

    root_logger = logging.getLogger()
    root_logger.setLevel(settings.log_level.upper())
    root_logger.handlers.clear()

    log_format = (
        "%(asctime)s %(levelname)s %(name)s %(message)s "
        "%(service_name)s %(instance_id)s"
    )

    formatter = JsonFormatter(log_format)

    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    console_handler.addFilter(_ServiceContextFilter())

    app_file_handler = RotatingFileHandler(
        log_dir / "app.log",
        maxBytes=5_000_000,
        backupCount=3,
        encoding="utf-8",
    )
    app_file_handler.setFormatter(formatter)
    app_file_handler.addFilter(_ServiceContextFilter())

    error_file_handler = RotatingFileHandler(
        log_dir / "errors.log",
        maxBytes=5_000_000,
        backupCount=3,
        encoding="utf-8",
    )
    error_file_handler.setLevel(logging.ERROR)
    error_file_handler.setFormatter(formatter)
    error_file_handler.addFilter(_ServiceContextFilter())

    root_logger.addHandler(console_handler)
    root_logger.addHandler(app_file_handler)
    root_logger.addHandler(error_file_handler)


class _ServiceContextFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        settings = get_settings()

        # Include service/container context so logs remain useful when API and workers run separately.
        record.service_name = settings.service_name
        record.instance_id = os.getenv("HOSTNAME", "local")
        return True