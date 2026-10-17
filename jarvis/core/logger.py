"""Logging configuration for Jarvis Voice Assistant."""

import logging
import sys


def setup_logger(verbose: bool = False) -> logging.Logger:
    """Configure structured console logging for Jarvis."""
    root_logger = logging.getLogger("jarvis")
    level = logging.DEBUG if verbose else logging.INFO
    root_logger.setLevel(level)

    # Avoid duplicate handlers if called multiple times
    if not root_logger.handlers:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(level)
        formatter = logging.Formatter(
            fmt="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
            datefmt="%H:%M:%S",
        )
        console_handler.setFormatter(formatter)
        root_logger.addHandler(console_handler)

    return root_logger
