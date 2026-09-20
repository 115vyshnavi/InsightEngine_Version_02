"""InsightEngine Structured Logging System."""

import logging
import sys
from app.core.config import settings


def setup_logger(name: str = "insightengine") -> logging.Logger:
    """Configures and returns a structured logger."""
    logger = logging.getLogger(name)

    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        formatter = logging.Formatter(
            fmt="%(asctime)s | %(levelname)-7s | [%(name)s:%(filename)s:%(lineno)d] - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)

    level_name = getattr(settings, "LOG_LEVEL", "INFO").upper()
    logger.setLevel(getattr(logging, level_name, logging.INFO))
    return logger


logger = setup_logger("insightengine")
