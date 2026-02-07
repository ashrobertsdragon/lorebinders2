import logging
import os
import sys
from pathlib import Path


def configure_logging(
    log_file: Path | None = None,
    verbose: bool = False,
    level: int | str | None = None,
) -> None:
    """Configure logging to console and optionally to a file.

    Args:
        log_file: Path to the log file.
        verbose: fast way to set logging to DEBUG.
        level: logging level.
    """
    logger = logging.getLogger("lorebinders")

    if level is None:
        env_level = os.getenv("LOREBINDERS_LOG_LEVEL", "INFO").upper()
        level = getattr(logging, env_level, logging.INFO)

    if verbose:
        level = logging.DEBUG

    logger.setLevel(level)

    if logger.handlers:
        return

    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )

    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    if log_file:
        file_handler = logging.FileHandler(log_file, encoding="utf-8")
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
        logger.info(f"Logging to file: {log_file}")
