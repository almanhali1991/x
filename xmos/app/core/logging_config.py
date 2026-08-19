"""
Core logging configuration for XMOS.

Provides structured logging with redaction of sensitive data.
"""

import logging
import sys
from pathlib import Path
from datetime import datetime
from typing import Any

from app.core.config import settings
from app.core.security import redact_dict


class RedactingFilter(logging.Filter):
    """Filter that redacts sensitive data from log records."""

    SENSITIVE_KEYS = [
        "password",
        "secret",
        "token",
        "key",
        "api_key",
        "access_token",
        "refresh_token",
        "client_secret",
        "bearer",
    ]

    def filter(self, record: logging.LogRecord) -> bool:
        """Redact sensitive data from log message and args."""
        # Redact in message args
        if record.args:
            if isinstance(record.args, dict):
                record.args = redact_dict(record.args, self.SENSITIVE_KEYS)
            elif isinstance(record.args, tuple):
                record.args = tuple(
                    redact_dict(arg, self.SENSITIVE_KEYS) if isinstance(arg, dict) else arg
                    for arg in record.args
                )

        return True


def setup_logging() -> logging.Logger:
    """
    Configure application logging.

    Returns:
        Configured logger instance
    """
    # Create logs directory
    log_path = Path(settings.log_file)
    log_path.parent.mkdir(parents=True, exist_ok=True)

    # Get root logger
    logger = logging.getLogger("xmos")
    logger.setLevel(getattr(logging, settings.log_level.upper(), logging.INFO))

    # Clear existing handlers
    logger.handlers.clear()

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.DEBUG if settings.is_development else logging.INFO)
    console_formatter = logging.Formatter(
        fmt="%(asctime)s | %(levelname)-8s | %(name)s:%(lineno)d | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    console_handler.setFormatter(console_formatter)
    console_handler.addFilter(RedactingFilter())
    logger.addHandler(console_handler)

    # File handler (rotation handled externally or by systemd)
    file_handler = logging.FileHandler(log_path, encoding="utf-8")
    file_handler.setLevel(logging.DEBUG)
    file_formatter = logging.Formatter(
        fmt="%(asctime)s | %(levelname)-8s | %(name)s:%(lineno)d | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    file_handler.setFormatter(file_formatter)
    file_handler.addFilter(RedactingFilter())
    logger.addHandler(file_handler)

    return logger


def get_logger(name: str) -> logging.Logger:
    """
    Get a child logger with the xmos prefix.

    Args:
        name: Logger name (will be prefixed with 'xmos.')

    Returns:
        Configured logger instance
    """
    return logging.getLogger(f"xmos.{name}")


# Default application logger
logger = setup_logging()


def log_startup() -> None:
    """Log application startup information."""
    logger.info("=" * 60)
    logger.info("XMOS - X Marketing Operating System Starting")
    logger.info("=" * 60)
    logger.info(f"Environment: {settings.app_env}")
    logger.info(f"Debug Mode: {settings.app_debug}")
    logger.info(f"Host: {settings.app_host}:{settings.app_port}")
    logger.info(f"Timezone: {settings.app_timezone}")
    logger.info(f"Database: {settings.database_url}")
    logger.info("=" * 60)


def log_shutdown() -> None:
    """Log application shutdown."""
    logger.info("=" * 60)
    logger.info("XMOS Shutting Down")
    logger.info("=" * 60)


class LogContext:
    """Context manager for adding contextual information to logs."""

    def __init__(self, **context: Any):
        self.context = context
        self.logger = logging.getLogger("xmos")

    def __enter__(self) -> "LogContext":
        self.logger.debug(f"Context entered: {redact_dict(self.context)}")
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> bool:
        if exc_type is not None:
            self.logger.error(
                f"Context exited with error: {exc_type.__name__}: {exc_val}",
                extra={"context": redact_dict(self.context)},
            )
        else:
            self.logger.debug(f"Context exited successfully: {redact_dict(self.context)}")
        return False  # Don't suppress exceptions
