"""
Logging configuration for CrossInsure AI backend.
Sets up structured logging with audit trail capabilities.
"""

import logging
import logging.config
from app.core.config import settings

LOGGING_CONFIG = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "default": {
            "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        },
        "detailed": {
            "format": "%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s",
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "level": settings.log_level,
            "formatter": "detailed",
            "stream": "ext://sys.stdout",
        },
        "file": {
            "class": "logging.handlers.RotatingFileHandler",
            "level": settings.log_level,
            "formatter": "detailed",
            "filename": "logs/crossinsure_ai.log",
            "maxBytes": 10485760,  # 10 MB
            "backupCount": 5,
        },
        "audit": {
            "class": "logging.handlers.RotatingFileHandler",
            "level": "INFO",
            "formatter": "detailed",
            "filename": "logs/audit_trail.log",
            "maxBytes": 10485760,  # 10 MB
            "backupCount": 10,
        },
    },
    "loggers": {
        "": {
            "level": settings.log_level,
            "handlers": ["console", "file"],
        },
        "audit": {
            "level": "INFO",
            "handlers": ["audit"],
            "propagate": False,
        },
    },
}


def setup_logging():
    """Initialize logging configuration."""
    logging.config.dictConfig(LOGGING_CONFIG)


def get_logger(name: str) -> logging.Logger:
    """Get a logger instance by name."""
    return logging.getLogger(name)


def get_audit_logger() -> logging.Logger:
    """Get the audit logger for compliance tracking."""
    return logging.getLogger("audit")
