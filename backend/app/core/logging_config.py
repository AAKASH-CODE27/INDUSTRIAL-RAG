import logging
import os

from app.core.config import LOG_LEVEL


def setup_logging(level: int | None = None) -> None:
    log_level = level if level is not None else getattr(logging, LOG_LEVEL, logging.INFO)
    logging.basicConfig(
        level=log_level,
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
        force=True,
    )


def get_logger(name: str) -> logging.Logger:
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, LOG_LEVEL, logging.INFO))
    return logger
