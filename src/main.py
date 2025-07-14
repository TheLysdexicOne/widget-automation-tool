#!/usr/bin/env python3
"""
Widget Automation Tool - Main Entry Point

This is the main entry point for the Widget Automation Tool application.
It handles command line arguments and initializes the appropriate components.
"""

import sys
import argparse
import logging
from pathlib import Path

# Add src directory to Python path
sys.path.insert(0, str(Path(__file__).parent))

from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt
from core.application import WidgetAutomationApp


def setup_logging(debug=False):
    """Setup logging configuration."""
    level = logging.DEBUG if debug else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[
            logging.FileHandler("widget_automation.log"),
            logging.StreamHandler(sys.stdout) if debug else logging.NullHandler(),
        ],
    )
    return logging.getLogger(__name__)


def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Widget Automation Tool", prog="widget-automation-tool"
    )

    parser.add_argument(
        "--debug", action="store_true", help="Launch with debug console visible"
    )

    parser.add_argument(
        "--tests", action="store_true", help="Run automated tests and exit"
    )

    parser.add_argument(
        "--target",
        default="WidgetInc.exe",
        help="Target process name to monitor (default: WidgetInc.exe)",
    )

    parser.add_argument(
        "--version", action="version", version="Widget Automation Tool 1.0.0"
    )

    return parser.parse_args()


def main():
    """Main application entry point."""
    args = parse_arguments()
    logger = setup_logging(args.debug)

    logger.info("Starting Widget Automation Tool...")
    logger.info(f"Debug mode: {args.debug}")
    logger.info(f"Test mode: {args.tests}")

    # Create QApplication
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)  # Keep running when windows are closed

    # Create main application
    widget_app = WidgetAutomationApp(
        debug_mode=args.debug, test_mode=args.tests, target_process=args.target
    )

    if args.tests:
        # Run tests and exit
        logger.info("Running automated tests...")
        result = widget_app.run_tests()
        logger.info(f"Tests completed with result: {result}")
        return result

    # Start the application
    logger.info("Application initialized successfully")
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
