"""
Stylesheet Loader - Simple QSS File Loading

This module provides a simple way to load QSS files for PyQt6 applications.
"""

import logging
from pathlib import Path
from typing import Optional


def load_stylesheet(filename: str) -> str:
    """Load a QSS stylesheet file and return its contents."""
    logger = logging.getLogger(__name__)

    # Look for the file in the assets/styles directory
    styles_dir = Path(__file__).parent.parent.parent / "assets" / "styles"
    qss_file = styles_dir / filename

    if not qss_file.exists():
        logger.warning(f"Stylesheet file not found: {qss_file}")
        return ""

    try:
        with open(qss_file, "r", encoding="utf-8") as f:
            stylesheet = f.read()

        logger.debug(f"Loaded stylesheet: {qss_file}")
        return stylesheet

    except Exception as e:
        logger.error(f"Error loading stylesheet {qss_file}: {e}")
        return ""


def get_main_stylesheet() -> str:
    """Get the main application stylesheet."""
    return load_stylesheet("main.qss")
