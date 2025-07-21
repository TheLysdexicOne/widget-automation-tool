#!/usr/bin/env python3
"""
Widget Automation Tool - Main Entry Point

Clean, simplified overlay-based automation tool for WidgetInc.exe.
"""

import sys
import argparse
import logging
import signal
from pathlib import Path

# Add src directory to Python path
sys.path.insert(0, str(Path(__file__).parent))

from PyQt6.QtWidgets import QApplication
from overlay.main_overlay import MainOverlayWidget


def setup_logging(debug=False):
    """Setup logging configuration."""
    logs_dir = Path(__file__).parent.parent / "logs"
    logs_dir.mkdir(exist_ok=True)

    # Simple log setup - one file, rotate when large
    log_file = logs_dir / "widget_automation.log"

    # Basic cleanup - keep log files under 10MB
    if log_file.exists() and log_file.stat().st_size > 10 * 1024 * 1024:
        backup_file = logs_dir / "widget_automation.log.bak"
        if backup_file.exists():
            backup_file.unlink()
        log_file.rename(backup_file)

    level = logging.DEBUG if debug else logging.INFO
    format_str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

    # Configure root logger
    logging.basicConfig(
        level=level,
        format=format_str,
        handlers=[
            logging.FileHandler(log_file, mode="a"),
            logging.StreamHandler(sys.stdout) if debug else logging.NullHandler(),
        ],
    )

    return logging.getLogger(__name__)


def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Widget Automation Tool", prog="widget-automation-tool")
    parser.add_argument("--debug", action="store_true", help="Enable debug output to console")
    parser.add_argument("--target", default="WidgetInc.exe", help="Target process name (default: WidgetInc.exe)")
    parser.add_argument("--version", action="version", version="Widget Automation Tool 2.0.0")
    return parser.parse_args()


def main():
    """Main application entry point."""
    args = parse_arguments()
    logger = setup_logging(args.debug)

    logger.info("Starting Widget Automation Tool...")
    if args.debug:
        logger.info(f"Debug mode enabled, target: {args.target}")

    # Create QApplication
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)

    # Create main overlay widget
    overlay = MainOverlayWidget(target_process=args.target, debug_mode=args.debug)

    # Setup clean shutdown
    def shutdown_handler(signum, frame):
        logger.info(f"Signal {signum} received, shutting down...")
        overlay.shutdown()
        app.quit()
        sys.exit(0)

    signal.signal(signal.SIGINT, shutdown_handler)
    signal.signal(signal.SIGTERM, shutdown_handler)

    # Start the application
    logger.info("Application initialized successfully")
    overlay.show()

    try:
        return app.exec()
    except KeyboardInterrupt:
        logger.info("Keyboard interrupt, shutting down...")
        overlay.shutdown()
        return 0
    except Exception as e:
        logger.error(f"Application error: {e}")
        overlay.shutdown()
        return 1


if __name__ == "__main__":
    sys.exit(main())
