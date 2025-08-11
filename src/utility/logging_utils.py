"""
Logging utilities for the Widget Automation Tool.
Provides centralized logging configuration with timestamped files and console output.
"""

import gzip
import logging
import sys
import time
from datetime import datetime
from pathlib import Path


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


class DeduplicatingFilter(logging.Filter):
    """Filter that suppresses consecutive repeated log messages and logs summaries instead."""

    def __init__(self, max_repeat_time=2.0, max_repeat_count=500):
        super().__init__()
        self.max_repeat_time = max_repeat_time
        self.max_repeat_count = max_repeat_count
        self.last_message = None
        self.consecutive_count = 0
        self.first_repeat_time = None
        # Fuzzy pattern tracking
        self.fuzzy_pattern = None
        self.fuzzy_count = 0
        self.fuzzy_coordinates = []
        self.first_fuzzy_time = None

    def extract_click_pattern(self, message):
        """Extract click pattern from message, return base pattern and coordinates if matched."""
        import re

        # Pattern for click messages: "Clicked at (x, y) with {button} button"
        click_pattern = r"Clicked at \((-?\d+), (-?\d+)\) with (\w+) button"
        match = re.match(click_pattern, message)

        if match:
            x, y, button = match.groups()
            base_pattern = f"Clicked at {{coords}} with {button} button"
            return base_pattern, (int(x), int(y))

        return None, None

    def is_fuzzy_match(self, message, pattern):
        """Check if message matches the fuzzy pattern."""
        if not pattern:
            return False

        base_pattern, coords = self.extract_click_pattern(message)
        return base_pattern == pattern

    def filter(self, record):
        """Filter consecutive repeated messages and emit summaries."""
        message = record.getMessage()
        current_time = time.time()

        # Check for fuzzy pattern matching (like rapid clicks)
        base_pattern, coords = self.extract_click_pattern(message)

        if base_pattern:
            # This is a click message - check for fuzzy pattern
            if self.fuzzy_pattern == base_pattern:
                # Same click pattern, accumulate
                self.fuzzy_count += 1
                self.fuzzy_coordinates.append(coords)
                if self.first_fuzzy_time is None:
                    self.first_fuzzy_time = current_time

                time_diff = current_time - self.first_fuzzy_time

                # Emit summary if thresholds reached
                if self.fuzzy_count >= 99999 or time_diff >= 2.0:
                    coord_summary = f"({len(self.fuzzy_coordinates)} locations)"
                    summary_msg = base_pattern.replace("{coords}", coord_summary)
                    summary_msg += f" | {self.fuzzy_count} rapid clicks over {time_diff:.1f} seconds"

                    record.msg = summary_msg
                    record.args = ()

                    # Reset fuzzy tracking
                    self.fuzzy_pattern = None
                    self.fuzzy_count = 0
                    self.fuzzy_coordinates = []
                    self.first_fuzzy_time = None

                    return True
                else:
                    # Still accumulating, suppress this one
                    return False
            else:
                # Different or new click pattern
                if self.fuzzy_count > 3 and self.fuzzy_pattern:
                    # Emit summary for previous pattern first
                    time_diff = current_time - self.first_fuzzy_time if self.first_fuzzy_time else 0
                    coord_summary = f"({len(self.fuzzy_coordinates)} locations)"
                    summary_msg = self.fuzzy_pattern.replace("{coords}", coord_summary)
                    summary_msg += f" | {self.fuzzy_count} rapid clicks over {time_diff:.1f} seconds"

                    record.msg = summary_msg
                    record.args = ()

                    # Start tracking new pattern
                    self.fuzzy_pattern = base_pattern
                    self.fuzzy_count = 1
                    self.fuzzy_coordinates = [coords]
                    self.first_fuzzy_time = None

                    return True
                else:
                    # Start tracking new pattern or show accumulated clicks if not enough
                    if self.fuzzy_count > 1 and self.fuzzy_pattern:
                        # Show the accumulated clicks normally since not enough for summary
                        self.fuzzy_pattern = None
                        self.fuzzy_count = 0
                        self.fuzzy_coordinates = []
                        self.first_fuzzy_time = None

                    self.fuzzy_pattern = base_pattern
                    self.fuzzy_count = 1
                    self.fuzzy_coordinates = [coords]
                    self.first_fuzzy_time = None
                    return True
        else:
            # Not a click message - handle previous fuzzy pattern if exists
            if self.fuzzy_count > 3 and self.fuzzy_pattern:
                # Emit summary for accumulated fuzzy pattern
                time_diff = current_time - self.first_fuzzy_time if self.first_fuzzy_time else 0
                coord_summary = f"({len(self.fuzzy_coordinates)} locations)"
                summary_msg = self.fuzzy_pattern.replace("{coords}", coord_summary)
                summary_msg += f" | {self.fuzzy_count} rapid clicks over {time_diff:.1f} seconds"

                record.msg = summary_msg
                record.args = ()

                # Reset fuzzy tracking
                self.fuzzy_pattern = None
                self.fuzzy_count = 0
                self.fuzzy_coordinates = []
                self.first_fuzzy_time = None

                return True

        # Reset fuzzy tracking for non-click messages
        if not base_pattern:
            self.fuzzy_pattern = None
            self.fuzzy_count = 0
            self.fuzzy_coordinates = []
            self.first_fuzzy_time = None

        # Original exact duplicate logic for non-click messages
        if message == self.last_message:
            # This is a consecutive repeat
            self.consecutive_count += 1
            if self.first_repeat_time is None:
                self.first_repeat_time = current_time

            time_diff = current_time - self.first_repeat_time

            if self.consecutive_count >= self.max_repeat_count or time_diff >= self.max_repeat_time:
                # Emit summary and reset
                if self.consecutive_count > 1:
                    summary_msg = f"{message} | Repeated {self.consecutive_count} times over {time_diff:.1f} seconds"

                    record.msg = summary_msg
                    record.args = ()

                    # Reset tracking
                    self.last_message = None
                    self.consecutive_count = 0
                    self.first_repeat_time = None

                    return True
                else:
                    # Single occurrence, just show it
                    self.last_message = None
                    self.consecutive_count = 0
                    self.first_repeat_time = None
                    return True
            else:
                # Still accumulating repeats, suppress this one
                return False
        else:
            # Different message - emit previous summary if we had repeats
            if self.consecutive_count > 1:
                # We have accumulated repeats, need to emit summary first
                time_diff = current_time - self.first_repeat_time if self.first_repeat_time else 0
                summary_msg = (
                    f"{self.last_message} | Repeated {self.consecutive_count} times over {time_diff:.1f} seconds"
                )

                # Modify current record to show the summary
                record.msg = summary_msg
                record.args = ()

                # Reset tracking for the new message
                self.last_message = message
                self.consecutive_count = 1
                self.first_repeat_time = None

                return True
            else:
                # No accumulated repeats, just track this new message
                self.last_message = message
                self.consecutive_count = 1
                self.first_repeat_time = None
                return True


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


def setup_logging():
    """Setup logging configuration with timestamped files and debug-to-file always."""
    # Check if debug argument is passed
    debug_mode = "--debug" in sys.argv or "-d" in sys.argv

    # Create logs directory
    logs_dir = Path(__file__).parent.parent.parent / "logs"
    logs_dir.mkdir(exist_ok=True)

    # Manage existing log files (compress old ones)
    manage_log_files(logs_dir, "widget", keep_count=5)

    # Setup logging formats - different for file vs console
    file_format = "%(asctime)s | %(name_clean)-20s | %(levelname)-8s | %(message)s"
    console_format = "%(asctime)s | %(name_clean)-20s | %(levelname_short)s | %(message)s"

    # Custom formatter base class that cleans logger names
    class BaseCustomFormatter(logging.Formatter):
        def format(self, record):
            # Clean the logger name: remove "Automator" suffix and limit to 20 chars
            name = record.name
            if name.endswith("Automator"):
                name = name[:-9]  # Remove "Automator" (9 characters)

            # Truncate to 20 characters if still too long
            if len(name) > 20:
                name = name[:20]

            record.name_clean = name
            return super().format(record)

    # Custom formatter class for console with truncated level names
    class ConsoleFormatter(BaseCustomFormatter):
        def format(self, record):
            # Add truncated level name
            level_map = {"DEBUG": "D", "INFO": "I", "WARNING": "W", "ERROR": "E", "CRITICAL": "C"}
            record.levelname_short = level_map.get(record.levelname, record.levelname[0])
            return super().format(record)

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
    file_handler.setFormatter(BaseCustomFormatter(file_format, datefmt="%Y-%m-%d %H:%M:%S"))
    file_handler.addFilter(DeduplicatingFilter(max_repeat_time=2.0, max_repeat_count=999999))

    # Setup console handler - level depends on debug mode
    console_handler = logging.StreamHandler(sys.stdout)
    if debug_mode:
        console_handler.setLevel(logging.DEBUG)  # Debug mode: show debug in console
        root_logger.setLevel(logging.DEBUG)
    else:
        console_handler.setLevel(logging.INFO)  # Normal mode: only info+ in console
        root_logger.setLevel(logging.DEBUG)  # But root logger still at DEBUG for file

    console_handler.setFormatter(ConsoleFormatter(console_format, datefmt="%Y-%m-%d %H:%M:%S"))
    console_handler.addFilter(DeduplicatingFilter(max_repeat_time=2.0, max_repeat_count=999999))

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
