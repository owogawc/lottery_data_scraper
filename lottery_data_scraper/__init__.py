"""
Configure logging for the entire package.

You can specify a log level with the environment variable
PY_LOG_LVL=[debug|info|warning|error|critical]
"""
import logging
import logging.config
import os


# Prefix the basic format with a timestamp, file pathname, and line number.
# See: https://docs.python.org/3/library/logging.html#logrecord-attributes
LOG_FORMAT = "%(asctime)s %(pathname)s %(lineno)s {}".format(logging.BASIC_FORMAT)

log_level = getattr(logging, os.environ.get("PY_LOG_LVL", "WARNING").upper())
logging_config = {
    "version": 1,
    "formatters": {
        "standard": {
            "format": LOG_FORMAT,
        },
    },
    "handlers": {
        "default": {
            "level": log_level,
            "formatter": "standard",
            "class": "logging.StreamHandler",
        },
    },
    "loggers": {
        "": {
            "handlers": ["default"],
            "level": log_level,
            "propagate": True,
        },
    },
}

logging.config.dictConfig(logging_config)
