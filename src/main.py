#!/usr/bin/env python3
"""
Widget Automation Tool - Main Entry Point

Clean, simplified overlay-based automation tool for WidgetInc.exe.
"""

import sys
import argparse
import logging
import signal
import os
from pathlib import Path

# Add src directory to Python path
sys.path.insert(0, str(Path(__file__).parent))

from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt
from overlay.main_overlay import MainOverlayWidget


def setup_logging(debug=False):
    """Setup logging configuration with file rotation."""
    logs_dir = Path(__file__).parent.parent / "logs"
    logs_dir.mkdir(exist_ok=True)

    # Clean up old logs (keep max 5 of each)
    _cleanup_old_logs(logs_dir, "info.log", max_files=5)
    _cleanup_old_logs(logs_dir, "debug.log", max_files=5)

    # Configure logging
    log_level = logging.DEBUG if debug else logging.INFO

    # File handlers
    info_handler = logging.FileHandler(logs_dir / "info.log", mode="a")
    info_handler.setLevel(logging.INFO)
    info_handler.setFormatter(
        logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    )

    debug_handler = logging.FileHandler(logs_dir / "debug.log", mode="a")
    debug_handler.setLevel(logging.DEBUG)
    debug_handler.setFormatter(
        logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    )

    # Console handler (only if debug mode)
    handlers = [info_handler, debug_handler]
    if debug:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.DEBUG)
        console_handler.setFormatter(
            logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
        )
        handlers.append(console_handler)

    # Configure root logger
    logging.basicConfig(level=log_level, handlers=handlers)

    return logging.getLogger(__name__)


def _cleanup_old_logs(logs_dir: Path, base_name: str, max_files: int = 5):
    """Clean up old log files, keeping only the most recent ones."""
    pattern = base_name.replace(".log", "*.log")
    log_files = sorted(
        logs_dir.glob(pattern), key=lambda f: f.stat().st_mtime, reverse=True
    )

    # Remove files beyond the max_files limit
    for old_file in log_files[max_files:]:
        try:
            old_file.unlink()
        except Exception:
            pass


def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Widget Automation Tool", prog="widget-automation-tool"
    )

    parser.add_argument(
        "--debug", action="store_true", help="Enable debug output to console"
    )

    parser.add_argument(
        "--target",
        default="WidgetInc.exe",
        help="Target process name to monitor (default: WidgetInc.exe)",
    )

    parser.add_argument(
        "--version", action="version", version="Widget Automation Tool 2.0.0"
    )

    return parser.parse_args()


def main():
    """Main application entry point."""
    args = parse_arguments()
    logger = setup_logging(args.debug)

    logger.info("Starting Widget Automation Tool...")
    logger.info(f"Debug mode: {args.debug}")
    logger.info(f"Target process: {args.target}")

    # Create QApplication
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)  # Keep running when overlay is hidden

    # Create main overlay widget
    overlay = MainOverlayWidget(target_process=args.target, debug_mode=args.debug)

    # Setup signal handlers for clean shutdown
    def signal_handler(signum, frame):
        logger.info(f"Received signal {signum}, shutting down gracefully...")
        try:
            overlay.shutdown()
            app.processEvents()  # Process any pending events
            app.quit()
        except:
            pass
        sys.exit(0)

    # Handle Ctrl+C (SIGINT) and other termination signals
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    # Start the application
    logger.info("Application initialized successfully")
    overlay.show()

    try:
        return app.exec()
    except KeyboardInterrupt:
        logger.info("KeyboardInterrupt received, shutting down...")
        try:
            overlay.shutdown()
            app.processEvents()
        except:
            pass
        return 0
    except Exception as e:
        logger.error(f"Application error: {e}")
        try:
            overlay.shutdown()
            app.processEvents()
        except:
            pass
        return 1
    finally:
        # Final cleanup
        try:
            app.quit()
        except:
            pass


if __name__ == "__main__":
    sys.exit(main())
