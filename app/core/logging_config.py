"""
Logging configuration for CrossInsure AI backend.
Sets up structured logging with audit trail capabilities.
"""

import logging
import logging.config
import os
from pathlib import Path
from app.core.config import settings


def setup_logging():
    """Initialize logging configuration."""
    # Create logs directory if it doesn't exist (for local dev)
    logs_dir = Path("logs")
    try:
        logs_dir.mkdir(exist_ok=True)
        use_file_handlers = True
    except (OSError, PermissionError):
        # In production environments like Render, we might not have write access
        use_file_handlers = False
    
    # Build handlers list dynamically
    handlers = ["console"]
    logging_handlers = {
        "console": {
            "class": "logging.StreamHandler",
            "level": settings.log_level,
            "formatter": "detailed",
            "stream": "ext://sys.stdout",
        },
    }
    
    # Only add file handlers if we can write to disk
    if use_file_handlers:
        logging_handlers["file"] = {
            "class": "logging.handlers.RotatingFileHandler",
            "level": settings.log_level,
            "formatter": "detailed",
            "filename": "logs/crossinsure_ai.log",
            "maxBytes": 10485760,  # 10 MB
            "backupCount": 5,
        }
        logging_handlers["audit"] = {
            "class": "logging.handlers.RotatingFileHandler",
            "level": "INFO",
            "formatter": "detailed",
            "filename": "logs/audit_trail.log",
            "maxBytes": 10485760,  # 10 MB
            "backupCount": 10,
        }
        handlers.append("file")
    
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
        "handlers": logging_handlers,
        "loggers": {
            "": {
                "level": settings.log_level,
                "handlers": handlers,
            },
            "audit": {
                "level": "INFO",
                "handlers": ["audit"] if use_file_handlers else ["console"],
                "propagate": False,
            },
        },
    }
    
    logging.config.dictConfig(LOGGING_CONFIG)


def get_logger(name: str) -> logging.Logger:
    """Get a logger instance by name."""
    return logging.getLogger(name)


def get_audit_logger() -> logging.Logger:
    """Get the audit logger for compliance tracking."""
    return logging.getLogger("audit")
