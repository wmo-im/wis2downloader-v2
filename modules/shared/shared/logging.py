"""Centralized logging configuration for wis2downloader modules."""
import logging
import os
import sys
import time
from typing import Optional


def setup_logging(name: Optional[str] = None, level: Optional[str] = None) -> logging.Logger:
    """
    Set up standardized logging with UTC timestamps.

    Args:
        name: Logger name (typically __name__). If None, configures root logger.
        level: Log level string. Defaults to LOG_LEVEL env var or DEBUG.

    Returns:
        Configured logger instance.
    """
    log_level = level or os.getenv("LOG_LEVEL", "DEBUG").upper()

    formatter = logging.Formatter(
        fmt='%(asctime)s.%(msecs)03dZ %(name)s %(levelname)s %(message)s',
        datefmt='%Y-%m-%dT%H:%M:%S'
    )
    formatter.converter = time.gmtime

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(formatter)

    if name is None:
        # Configure root logger
        logger = logging.getLogger()
        if logger.hasHandlers():
            logger.handlers.clear()
    else:
        logger = logging.getLogger(name)

    logger.setLevel(log_level)

    # Only add handler if not already present (avoid duplicates)
    if not any(isinstance(h, logging.StreamHandler) for h in logger.handlers):
        logger.addHandler(handler)

    return logger
