"""
Centralized logging configuration for CartaOS.

This module provides a standardized way to configure and use logging across the application.
It includes support for different log levels, file and console handlers, and structured logging.
"""

"""
Centralized logging configuration for CartaOS.

This module provides a standardized way to configure and use logging across the application.
It includes support for different log levels, file and console handlers, and structured logging.
"""

import json
import logging
import logging.handlers
import os
import sys
from datetime import datetime, timezone, UTC
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from pythonjsonlogger.json import JsonFormatter  # type: ignore


class CustomJsonFormatter(JsonFormatter):
    """Custom JSON formatter that includes additional context in log records."""

    def add_fields(
        self,
        log_record: Dict[str, Any],
        record: logging.LogRecord,
        message_dict: Dict[str, Any],
    ) -> None:
        """Add custom fields to the log record."""
        super().add_fields(log_record, record, message_dict)
        log_record["timestamp"] = datetime.now(UTC).isoformat()
        log_record["level"] = record.levelname
        log_record["logger"] = record.name
        log_record["module"] = record.module
        log_record["function"] = record.funcName
        log_record["line"] = record.lineno
        log_record["process"] = record.process
        log_record["thread"] = record.thread
        log_record["thread_name"] = record.threadName
        
        # Add any extra fields from the record's __dict__
        for key, value in record.__dict__.items():
            if key not in self._skip_fields and not key.startswith('_'):
                log_record[key] = value
                
        # Handle extra fields passed via the extra parameter
        if hasattr(record, 'extra') and isinstance(record.extra, dict):
            for key, value in record.extra.items():
                log_record[key] = value

        # Add exception info if present
        if record.exc_info:
            log_record["exception"] = self.formatException(record.exc_info)


class LogLevelFilter(logging.Filter):
    """Filter log records based on log level."""

    def __init__(self, level: int) -> None:
        """Initialize with the level to filter at."""
        self.level = level
        super().__init__()

    def filter(self, record: logging.LogRecord) -> bool:
        """Filter records at or above the specified level."""
        return record.levelno >= self.level


def setup_logging(
    log_level: Union[str, int] = logging.INFO,
    log_file: Optional[Union[str, Path]] = None,
    log_format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    json_format: bool = False,
    max_bytes: int = 10 * 1024 * 1024,  # 10MB
    backup_count: int = 5,
) -> None:
    """
    Configure logging for the application.

    Args:
        log_level: The logging level (e.g., 'INFO', 'DEBUG', logging.INFO).
        log_file: Path to the log file. If None, logs only to console.
        log_format: Format string for log messages.
        json_format: If True, logs will be in JSON format.
        max_bytes: Maximum log file size in bytes before rotation.
        backup_count: Number of backup log files to keep.
    """
    # Convert string log level to int if needed
    if isinstance(log_level, str):
        log_level = getattr(logging, log_level.upper(), logging.INFO)

    # Get the root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)

    # Clear any existing handlers
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)

    # Create formatters
    if json_format:
        formatter = CustomJsonFormatter(
            "%(timestamp)s %(level)s %(name)s %(module)s.%(function)s:%(lineno)d %(message)s"
        )
    else:
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            datefmt='%Y-%m-%d %H:%M:%S'
        )

    # Console handler (always at INFO level)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(max(logging.INFO, log_level))
    console_handler.setFormatter(formatter)
    
    # Add filter to exclude debug logs from console
    if log_level <= logging.DEBUG:
        console_handler.addFilter(LogLevelFilter(logging.INFO))
    
    root_logger.addHandler(console_handler)

    # File handler if log_file is specified
    if log_file:
        log_file = Path(log_file)
        log_file.parent.mkdir(parents=True, exist_ok=True)

        file_handler = logging.handlers.RotatingFileHandler(
            log_file, maxBytes=max_bytes, backupCount=backup_count, encoding="utf-8"
        )
        file_handler.setLevel(log_level)
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)

    # Configure third-party loggers
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("requests").setLevel(logging.WARNING)
    logging.getLogger("pdfminer").setLevel(logging.WARNING)
    logging.getLogger("PIL").setLevel(logging.WARNING)
    logging.getLogger("matplotlib").setLevel(logging.WARNING)
    logging.getLogger("asyncio").setLevel(logging.WARNING)


def get_logger(name: Optional[str] = None) -> logging.Logger:
    """
    Get a logger instance with the given name.

    Args:
        name: The name of the logger. If None, returns the root logger.

    Returns:
        A configured logger instance.
    """
    logger = logging.getLogger(name or __name__)
    
    # Ensure logger has at least one handler to avoid "No handlers could be found" warnings
    if not logger.handlers and not logging.getLogger().handlers:
        setup_logging()
    
    return logger


class LogContext:
    """Context manager for logging with additional context."""

    def __init__(
        self, logger: logging.Logger, message: str, **context: Any
    ) -> None:
        """Initialize the log context.

        Args:
            logger: The logger to use.
            message: The log message.
            **context: Additional context to include in the log record.
        """
        self.logger = logger
        self.message = message
        self.context = context
        self.start_time = datetime.now(UTC)

    def __enter__(self) -> "LogContext":
        """Enter the context and log the start message."""
        self.logger.info(
            f"Starting: {self.message}",
            extra={"context": self.context, "event": "start"},
        )
        return self

    def __exit__(
        self, exc_type: Any, exc_val: Any, exc_tb: Any
    ) -> None:
        """Exit the context and log the end message with duration."""
        end_time = datetime.now(UTC)
        duration = (end_time - self.start_time).total_seconds()
        
        # Create a message with the duration
        duration_msg = f" (took {duration:.3f}s)"
        
        if exc_type is None:
            self.logger.info(
                f"Completed: {self.message}{duration_msg}",
                extra={
                    "context": self.context,
                    "duration_seconds": duration,
                    "event": "complete",
                },
            )
        else:
            self.logger.error(
                f"Failed: {self.message} - {str(exc_val)}{duration_msg}",
                extra={
                    "context": self.context,
                    "duration_seconds": duration,
                    "event": "error",
                    "exception_type": exc_type.__name__,
                    "exception": str(exc_val),
                },
                exc_info=True,
            )


# Initialize logging when the module is imported
# This can be overridden by calling setup_logging() with different parameters
setup_logging()
