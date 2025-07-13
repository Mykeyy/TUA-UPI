import logging
import logging.config

# Custom logging configuration to suppress noisy loggers
LOGGING_CONFIG = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "default": {
            "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        },
    },
    "handlers": {
        "default": {
            "formatter": "default",
            "class": "logging.StreamHandler",
            "stream": "ext://sys.stdout",
        },
    },
    "root": {
        "level": "WARNING",
        "handlers": ["default"],
    },
    "loggers": {
        "uvicorn": {
            "level": "WARNING",
            "handlers": ["default"],
            "propagate": False,
        },
        "uvicorn.error": {
            "level": "WARNING",
            "handlers": ["default"],
            "propagate": False,
        },
        "uvicorn.access": {
            "level": "ERROR",
            "handlers": ["default"],
            "propagate": False,
        },
        "sqlalchemy": {
            "level": "ERROR",
            "handlers": ["default"],
            "propagate": False,
        },
        "sqlalchemy.engine": {
            "level": "ERROR",
            "handlers": ["default"],
            "propagate": False,
        },
        "sqlalchemy.pool": {
            "level": "ERROR",
            "handlers": ["default"],
            "propagate": False,
        },
    },
}

# Apply the configuration
logging.config.dictConfig(LOGGING_CONFIG)
