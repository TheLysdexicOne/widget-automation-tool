"""
Logging utilities to reduce excessive debug output.
Implements smart logging with throttling and level management.
"""

import logging
import logging.handlers
import os
import sys
import time
from pathlib import Path
from typing import Any, Dict


class LoggerMixin:
    """Mixin class providing convenient logging methods for any class."""

    logger: logging.Logger  # Type hint for mixin

    def log_info(self, message: str):
        """Convenience method for info logging."""
        if hasattr(self, "logger"):
            self.logger.info(message)
        else:
            logging.getLogger(self.__class__.__name__).info(message)

    def log_debug(self, message: str):
        """Convenience method for debug logging."""
        if hasattr(self, "logger"):
            self.logger.debug(message)
        else:
            logging.getLogger(self.__class__.__name__).debug(message)

    def log_error(self, message: str):
        """Convenience method for error logging."""
        if hasattr(self, "logger"):
            self.logger.error(message)
        else:
            logging.getLogger(self.__class__.__name__).error(message)

    def log_warning(self, message: str):
        """Convenience method for warning logging."""
        if hasattr(self, "logger"):
            self.logger.warning(message)
        else:
            logging.getLogger(self.__class__.__name__).warning(message)


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

    def info_throttled(self, message: str, throttle_seconds: float | None = None):
        """Log info message with throttling."""
        self._log_throttled(message, self.logger.info, throttle_seconds)

    def debug_throttled(self, message: str, throttle_seconds: float | None = None):
        """Log debug message with throttling."""
        self._log_throttled(message, self.logger.debug, throttle_seconds)

    def _log_throttled(self, message: str, log_func: Any, throttle_seconds: float | None = None):
        """Internal throttled logging method."""
        throttle = throttle_seconds or self.throttle_time
        current_time = time.time()

        if message not in self.last_messages or (current_time - self.last_messages[message]) >= throttle:
            self.last_messages[message] = current_time
            log_func(message)


def get_smart_logger(name: str) -> ThrottledLogger:
    """Get a smart logger with throttling capabilities."""
    return ThrottledLogger(logging.getLogger(name))


def log_position_change(logger: Any, old_pos: tuple[Any, ...], new_pos: tuple[Any, ...], context: str = ""):
    """Smart logging for position changes - only logs when actually changed."""
    if old_pos != new_pos:
        logger.info(f"Position changed: {old_pos} -> {new_pos} {context}")


def log_state_change(logger: Any, old_state: Any, new_state: Any, context: str = ""):
    """Smart logging for state changes - only logs when actually changed."""
    if old_state != new_state:
        logger.info(f"State changed: {old_state} -> {new_state} {context}")


def reduce_logging_noise(logger_name: str, level: int = logging.WARNING):
    """Reduce logging noise for specific loggers."""
    logger = logging.getLogger(logger_name)
    logger.setLevel(level)


def setup_rotating_logs(log_dir: str = "logs", max_bytes: int = 5 * 1024 * 1024, backup_count: int = 4):
    """
    Setup rotating log files with size limits.

    Args:
        log_dir: Directory to store log files
        max_bytes: Maximum size per log file (default: 5MB)
        backup_count: Number of backup files to keep (default: 4, total 5 files)
    """
    # Create logs directory if it doesn't exist
    os.makedirs(log_dir, exist_ok=True)

    # Get root logger
    root_logger = logging.getLogger()

    # Remove existing handlers to avoid duplicates
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)

    # Setup rotating file handler
    log_file = os.path.join(log_dir, "widget_automation.log")
    file_handler = logging.handlers.RotatingFileHandler(
        log_file, maxBytes=max_bytes, backupCount=backup_count, encoding="utf-8"
    )

    # Setup formatter
    formatter = logging.Formatter(
        "%(asctime)s  |  %(name)-25s  |  %(levelname)-8s  |  %(message)s", datefmt="%Y-%m-%d %H:%M:%S"
    )
    file_handler.setFormatter(formatter)

    # Add handler to root logger
    root_logger.addHandler(file_handler)
    root_logger.setLevel(logging.INFO)

    # Optional: Add console handler for debug mode
    console_handler = logging.StreamHandler()
    console_formatter = logging.Formatter("%(asctime)s  |  %(name)-25s  |  %(levelname)-8s  |  %(message)s")
    console_handler.setFormatter(console_formatter)
    root_logger.addHandler(console_handler)

    logging.info(
        f"Log rotation configured: max {max_bytes / 1024 / 1024:.1f}MB per file, {backup_count + 1} files total"
    )


def setup_automation_logging(debug_mode: bool = False):
    """
    Setup logging specifically for automation with appropriate levels and rotation.

    Args:
        debug_mode: If True, enables debug level logging and console output
    """
    # Setup rotating logs first
    setup_rotating_logs()

    if debug_mode:
        # Enable debug logging for automation modules
        logging.getLogger("automation").setLevel(logging.DEBUG)
        logging.getLogger("__main__").setLevel(logging.DEBUG)
    else:
        # Reduce noise from frequent automation operations
        reduce_logging_noise("automation.automation_engine", logging.WARNING)  # Reduce click/color logging
        reduce_logging_noise("automation.global_hotkey_manager", logging.INFO)
        reduce_logging_noise("automation.automation_engine.AutomationEngine", logging.WARNING)  # Engine debug logs

        # Keep important automation events at INFO level
        logging.getLogger("automation").setLevel(logging.INFO)
        logging.getLogger("__main__").setLevel(logging.INFO)


def setup_logging():
    """Setup logging configuration based on command line arguments."""
    # Check if debug argument is passed
    debug_mode = "--debug" in sys.argv or "-d" in sys.argv

    # Create logs directory
    logs_dir = Path(__file__).parent.parent.parent / "logs"
    logs_dir.mkdir(exist_ok=True)

    # Configure logging level
    log_level = logging.DEBUG if debug_mode else logging.INFO

    # Setup logging format
    log_format = "%(asctime)s  |  %(name)-25s  |  %(levelname)-8s  |  %(message)s"

    # Configure root logger
    logging.basicConfig(
        level=log_level,
        format=log_format,
        handlers=[logging.FileHandler(logs_dir / "automation_overlay.log"), logging.StreamHandler(sys.stdout)],
    )

    logger = logging.getLogger(__name__)
    logger.info(f"Starting Widget Automation Tool - Debug mode: {debug_mode}")
    return logger
