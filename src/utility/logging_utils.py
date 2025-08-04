"""
Logging utilities to reduce excessive debug output.
Implements smart logging with throttling and level management.
"""

import gzip
import logging
import logging.handlers
import os
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict


class LoggerMixin:
    """Mixin class providing convenient logging methods for any class."""

    logging: logging.Logger  # Type hint for mixin

    def log_info(self, message: str):
        """Convenience method for info logging."""
        if hasattr(self, "logger"):
            self.logging.info(message)
        else:
            logging.getLogger(self.__class__.__name__).info(message)

    def log_debug(self, message: str):
        """Convenience method for debug logging."""
        if hasattr(self, "logger"):
            self.logging.debug(message)
        else:
            logging.getLogger(self.__class__.__name__).debug(message)

    def log_error(self, message: str):
        """Convenience method for error logging."""
        if hasattr(self, "logger"):
            self.logging.error(message)
        else:
            logging.getLogger(self.__class__.__name__).error(message)

    def log_warning(self, message: str):
        """Convenience method for warning logging."""
        if hasattr(self, "logger"):
            self.logging.warning(message)
        else:
            logging.getLogger(self.__class__.__name__).warning(message)


def check_and_force_rotation(log_file_path, max_bytes=5 * 1024 * 1024):
    """
    Check if log file exceeds max size and manually rotate if needed.
    This ensures logs are rotated even if the application was previously terminated improperly.

    Args:
        log_file_path: Path to the log file
        max_bytes: Maximum size in bytes before rotation (default: 5MB)
    """
    try:
        log_file = Path(log_file_path)
        if log_file.exists() and log_file.stat().st_size > max_bytes:
            # File exists and is too large, perform manual rotation
            for i in range(3, -1, -1):  # 3, 2, 1, 0
                # Shift existing backup files
                backup = log_file.with_suffix(f".log.{i}")
                next_backup = log_file.with_suffix(f".log.{i + 1}")
                if backup.exists():
                    if next_backup.exists():
                        next_backup.unlink()
                    backup.rename(next_backup)

            # Rename current log file to .log.1
            first_backup = log_file.with_suffix(".log.1")
            if first_backup.exists():
                first_backup.unlink()
            log_file.rename(first_backup)

            # Log will be created automatically by the handler
            logging.getLogger(__name__).info(
                f"Manually rotated log file: {log_file.name} (exceeded {max_bytes / 1024 / 1024:.1f}MB)"
            )
    except Exception as e:
        # Don't let rotation errors affect the application
        print(f"Error during log rotation: {e}")


def create_timestamped_log_filename(base_name: str = "widget") -> str:
    """Create a timestamped log filename for each application start."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return f"{base_name}_{timestamp}.log"


def manage_log_files(logs_dir: Path, base_name: str = "widget", keep_count: int = 4):
    """
    Manage log files: keep the most recent 'keep_count' files, append older ones to archive.log.gz.

    Args:
        logs_dir: Directory containing log files
        base_name: Base name of log files to manage
        keep_count: Number of recent log files to keep uncompressed
    """
    try:
        # Find all log files matching the pattern
        log_pattern = f"{base_name}_*.log"
        log_files = list(logs_dir.glob(log_pattern))

        # Sort by modification time, newest first
        log_files.sort(key=lambda f: f.stat().st_mtime, reverse=True)

        # Keep the most recent files, compress the rest into archive
        if len(log_files) > keep_count:
            files_to_archive = log_files[keep_count:]
            archive_file = logs_dir / "archive.log.gz"

            # Open archive in append mode (or create if doesn't exist)
            with gzip.open(archive_file, "at", encoding="utf-8") as archive:
                for log_file in files_to_archive:
                    try:
                        # Add separator and timestamp for each archived file
                        archive.write(f"\n{'=' * 80}\n")
                        archive.write(f"ARCHIVED LOG: {log_file.name}\n")
                        archive.write(f"ARCHIVED TIME: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                        archive.write(f"{'=' * 80}\n\n")

                        # Append the entire log file to the archive
                        with open(log_file, "r", encoding="utf-8") as f_in:
                            archive.write(f_in.read())

                        archive.write(f"\n{'=' * 80}\n")
                        archive.write(f"END OF {log_file.name}\n")
                        archive.write(f"{'=' * 80}\n\n")

                        # Remove original file after successful archiving
                        log_file.unlink()
                        print(f"Archived and removed: {log_file.name}")

                    except Exception as e:
                        print(f"Error archiving {log_file.name}: {e}")

        # Clean up old individual compressed files from previous system
        old_compressed_pattern = f"{base_name}_*.log.gz"
        old_compressed_files = list(logs_dir.glob(old_compressed_pattern))

        if old_compressed_files:
            print(f"Cleaning up {len(old_compressed_files)} old individual compressed files...")
            for old_file in old_compressed_files:
                try:
                    old_file.unlink()
                    print(f"Removed old compressed file: {old_file.name}")
                except Exception as e:
                    print(f"Error removing old compressed file {old_file.name}: {e}")

        # Clean up legacy automation_overlay files from previous naming convention
        if base_name == "widget":  # Only do this cleanup when using new naming
            legacy_log_files = list(logs_dir.glob("automation_overlay_*.log"))
            legacy_compressed_files = list(logs_dir.glob("automation_overlay_*.log.gz"))

            # Archive legacy log files to archive.log.gz
            if legacy_log_files:
                print(f"Migrating {len(legacy_log_files)} legacy automation_overlay log files...")
                archive_file = logs_dir / "archive.log.gz"

                with gzip.open(archive_file, "at", encoding="utf-8") as archive:
                    for log_file in legacy_log_files:
                        try:
                            # Add separator and timestamp for each archived file
                            archive.write(f"\n{'=' * 80}\n")
                            archive.write(f"ARCHIVED LOG: {log_file.name} (legacy migration)\n")
                            archive.write(f"ARCHIVED TIME: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                            archive.write(f"{'=' * 80}\n\n")

                            # Append the entire log file to the archive
                            with open(log_file, "r", encoding="utf-8") as f_in:
                                archive.write(f_in.read())

                            archive.write(f"\n{'=' * 80}\n")
                            archive.write(f"END OF {log_file.name}\n")
                            archive.write(f"{'=' * 80}\n\n")

                            # Remove original file after successful archiving
                            log_file.unlink()
                            print(f"Migrated and removed: {log_file.name}")

                        except Exception as e:
                            print(f"Error migrating {log_file.name}: {e}")

            # Clean up legacy compressed files
            if legacy_compressed_files:
                print(f"Cleaning up {len(legacy_compressed_files)} legacy automation_overlay compressed files...")
                for old_file in legacy_compressed_files:
                    try:
                        old_file.unlink()
                        print(f"Removed legacy compressed file: {old_file.name}")
                    except Exception as e:
                        print(f"Error removing legacy compressed file {old_file.name}: {e}")

    except Exception as e:
        print(f"Error managing log files: {e}")


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

    # Setup rotating file handler - use same log file as main app
    log_file = os.path.join(log_dir, "widget.log")
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
    Setup logging specifically for automation with appropriate levels.
    Now uses the same timestamped file approach as main logging.

    Args:
        debug_mode: If True, enables debug level console output
    """
    # Use the main setup_logging function for consistency
    logger = setup_logging()

    if not debug_mode:
        # Reduce noise from frequent automation operations in console only
        # File logging still captures everything at DEBUG level
        reduce_logging_noise("automation.automation_engine", logging.WARNING)
        reduce_logging_noise("automation.global_hotkey_manager", logging.INFO)
        reduce_logging_noise("automation.automation_engine.AutomationEngine", logging.WARNING)

        # Keep important automation events at INFO level for console
        logging.getLogger("automation").setLevel(logging.INFO)
        logging.getLogger("__main__").setLevel(logging.INFO)

    return logger


def setup_logging():
    """Setup logging configuration with timestamped files and debug-to-file always."""
    # Check if debug argument is passed
    debug_mode = "--debug" in sys.argv or "-d" in sys.argv

    # Create logs directory
    logs_dir = Path(__file__).parent.parent.parent / "logs"
    logs_dir.mkdir(exist_ok=True)

    # Manage existing log files (compress old ones)
    manage_log_files(logs_dir, "widget", keep_count=5)

    # Setup logging format
    log_format = "%(asctime)s  |  %(name)-25s  |  %(levelname)-8s  |  %(message)s"

    # Get root logger and clear existing handlers
    root_logger = logging.getLogger()
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)

    # Create timestamped log file for this session
    log_filename = create_timestamped_log_filename("widget")
    log_file = logs_dir / log_filename

    # Setup file handler - ALWAYS uses DEBUG level (logs everything to file)
    file_handler = logging.FileHandler(log_file, encoding="utf-8")
    file_handler.setLevel(logging.DEBUG)  # Always log debug to file
    file_handler.setFormatter(logging.Formatter(log_format, datefmt="%Y-%m-%d %H:%M:%S"))

    # Setup console handler - level depends on debug mode
    console_handler = logging.StreamHandler(sys.stdout)
    if debug_mode:
        console_handler.setLevel(logging.DEBUG)  # Debug mode: show debug in console
        root_logger.setLevel(logging.DEBUG)
    else:
        console_handler.setLevel(logging.INFO)  # Normal mode: only info+ in console
        root_logger.setLevel(logging.DEBUG)  # But root logger still at DEBUG for file

    console_handler.setFormatter(logging.Formatter(log_format, datefmt="%Y-%m-%d %H:%M:%S"))

    # Add handlers to root logger
    root_logger.addHandler(file_handler)
    root_logger.addHandler(console_handler)

    logger = logging.getLogger(__name__)
    logger.info(f"Starting Widget Automation Tool - Debug mode: {debug_mode}")
    logger.info(f"Log file: {log_filename}")
    logger.info("Logging setup: DEBUG always saved to file, console shows " + ("DEBUG+" if debug_mode else "INFO+"))

    # Show managed log files
    log_files = list(logs_dir.glob("widget_*.log"))
    compressed_files = list(logs_dir.glob("widget_*.log.gz"))
    if log_files or compressed_files:
        logger.info(f"Log management: {len(log_files)} active logs, {len(compressed_files)} compressed")

    return logger
