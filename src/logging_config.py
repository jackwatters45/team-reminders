# TODO: fix
# src/logging_config.py
import logging
import logging.config

# Basic logging config dictionary
LOGGING_CONFIG = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "default": {
            "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            "datefmt": "%Y-%m-%d %H:%M:%S",  # Optional: Add date format
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "default",
            "stream": "ext://sys.stdout",  # Explicitly send to stdout
        },
        # Optional: Add a file handler
        # "file": {
        #     "class": "logging.FileHandler",
        #     "formatter": "default",
        #     "filename": "app.log", # Log file name
        #     "encoding": "utf-8",
        # },
    },
    "root": {
        "handlers": ["console"],  # Add "file" here if using file handler
        "level": "INFO",  # Base level for the root logger
    },
    "loggers": {
        # Control levels for specific libraries
        "uvicorn.error": {"level": "WARNING"},  # Uvicorn errors
        "uvicorn.access": {
            "handlers": ["console"],
            "level": "WARNING",
            "propagate": False,
        },  # Quieter access logs
        "sqlalchemy.engine": {"level": "WARNING"},  # Set to INFO for SQL query logging
        "arq": {"level": "INFO"},  # Arq specific logs
    },
}


def setup_logging():
    """Apply the logging configuration."""
    logging.config.dictConfig(LOGGING_CONFIG)
    logging.getLogger(__name__).info("Logging configured.")
