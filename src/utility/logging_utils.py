"""
Logging utilities to reduce excessive debug output.
Implements smart logging with throttling and level management.
"""

import logging
import time
from typing import Dict, Any


class ThrottledLogger:
    """Logger wrapper that throttles repeated messages."""

    def __init__(self, logger: logging.Logger):
        self.logger = logger
        self.last_messages: Dict[str, float] = {}
        self.throttle_time = 1.0  # 1 second throttle by default

    def info(self, message: str):
        """Standard info logging."""
        self.logger.info(message)

    def debug(self, message: str):
        """Standard debug logging."""
        self.logger.debug(message)

    def error(self, message: str):
        """Standard error logging."""
        self.logger.error(message)

    def warning(self, message: str):
        """Standard warning logging."""
        self.logger.warning(message)

    def info_throttled(self, message: str, throttle_seconds: float = None):
        """Log info message with throttling."""
        self._log_throttled(message, self.logger.info, throttle_seconds)

    def debug_throttled(self, message: str, throttle_seconds: float = None):
        """Log debug message with throttling."""
        self._log_throttled(message, self.logger.debug, throttle_seconds)

    def _log_throttled(self, message: str, log_func, throttle_seconds: float = None):
        """Internal throttled logging method."""
        throttle = throttle_seconds or self.throttle_time
        current_time = time.time()

        if (
            message not in self.last_messages
            or (current_time - self.last_messages[message]) >= throttle
        ):
            self.last_messages[message] = current_time
            log_func(message)


def get_smart_logger(name: str) -> ThrottledLogger:
    """Get a smart logger with throttling capabilities."""
    return ThrottledLogger(logging.getLogger(name))


def log_position_change(logger, old_pos: tuple, new_pos: tuple, context: str = ""):
    """Smart logging for position changes - only logs when actually changed."""
    if old_pos != new_pos:
        logger.info(f"Position changed: {old_pos} -> {new_pos} {context}")


def log_state_change(logger, old_state: Any, new_state: Any, context: str = ""):
    """Smart logging for state changes - only logs when actually changed."""
    if old_state != new_state:
        logger.info(f"State changed: {old_state} -> {new_state} {context}")


def reduce_logging_noise(logger_name: str, level: int = logging.WARNING):
    """Reduce logging noise for specific loggers."""
    logger = logging.getLogger(logger_name)
    logger.setLevel(level)
