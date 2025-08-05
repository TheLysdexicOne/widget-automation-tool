"""
Logging utilities for the Widget Automation Tool.
Provides centralized logging configuration with timestamped files and console output.
"""

import gzip
import logging
import sys
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

    # Setup console handler - level depends on debug mode
    console_handler = logging.StreamHandler(sys.stdout)
    if debug_mode:
        console_handler.setLevel(logging.DEBUG)  # Debug mode: show debug in console
        root_logger.setLevel(logging.DEBUG)
    else:
        console_handler.setLevel(logging.INFO)  # Normal mode: only info+ in console
        root_logger.setLevel(logging.DEBUG)  # But root logger still at DEBUG for file

    console_handler.setFormatter(ConsoleFormatter(console_format, datefmt="%Y-%m-%d %H:%M:%S"))

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
