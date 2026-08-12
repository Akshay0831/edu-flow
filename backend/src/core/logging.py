"""
Logging configuration and utilities

This module provides centralized logging configuration and utilities for the application.
"""

import logging
import logging.config
import sys
from pathlib import Path
from typing import Optional


def setup_logging(log_level: str = "INFO", log_file: Optional[str] = None) -> None:
    """Setup logging configuration for the application."""
    
    # Create logs directory if it doesn't exist
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    
    # Configure structured logging
    logging.config.dictConfig({
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "standard": {
                "format": "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
            },
            "detailed": {
                "format": "%(asctime)s [%(levelname)s] %(name)s:%(lineno)d: %(message)s"
            },
            "json": {
                "()": structlog.stdlib.ProcessorFormatter,
                "processor": structlog.processors.JSONRenderer()
            }
        },
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "level": log_level,
                "formatter": "standard",
                "stream": sys.stdout
            },
            "file": {
                "class": "logging.handlers.RotatingFileHandler",
                "level": log_level,
                "formatter": "detailed",
                "filename": log_file or "logs/edu_flow.log",
                "maxBytes": 10 * 1024 * 1024,  # 10MB
                "backupCount": 5
            },
            "error_file": {
                "class": "logging.handlers.RotatingFileHandler",
                "level": "ERROR",
                "formatter": "detailed",
                "filename": log_file or "logs/errors.log",
                "maxBytes": 10 * 1024 * 1024,  # 10MB
                "backupCount": 5
            }
        },
        "loggers": {
            "": {
                "handlers": ["console", "file", "error_file"],
                "level": log_level,
                "propagate": False
            },
            "uvicorn": {
                "handlers": ["console", "file"],
                "level": "INFO",
                "propagate": False
            },
            "sqlalchemy": {
                "handlers": ["console", "file"],
                "level": "WARNING",
                "propagate": False
            }
        }
    })
    
    # Configure structlog if available
    try:
        import structlog
        structlog.configure(
            processors=[
                structlog.stdlib.filter_by_level,
                structlog.stdlib.add_logger_name,
                structlog.stdlib.add_log_level,
                structlog.stdlib.PositionalArgumentsFormatter(),
                structlog.processors.TimeStamper(fmt="iso"),
                structlog.processors.StackInfoRenderer(),
                structlog.processors.format_exc_info,
                structlog.processors.UnicodeDecoder(),
                structlog.stdlib.ProcessorFormatter()
            ],
            wrapper_class=structlog.stdlib.BoundLogger,
            logger_factory=structlog.stdlib.LoggerFactory(),
            cache_logger_on_first_use=True,
        )
    except ImportError:
        # structlog not available, use standard logging only
        pass


def get_logger(name: str) -> logging.Logger:
    """Get a logger instance with the specified name."""
    return logging.getLogger(name)


def setup_structured_logger(name: str):
    """Get a structured logger instance."""
    try:
        import structlog
        return structlog.get_logger(name)
    except ImportError:
        # Fall back to standard logger
        return get_logger(name)


class LoggerMixin:
    """Mixin class that provides logging capabilities to other classes."""
    
    @property
    def logger(self) -> logging.Logger:
        """Get a logger instance for this class."""
        return get_logger(self.__class__.__name__)
    
    @property
    def structured_logger(self):
        """Get a structured logger instance for this class."""
        return setup_structured_logger(self.__class__.__name__)