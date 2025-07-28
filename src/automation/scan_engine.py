"""
Scan Engine
Handles color detection and scanning operations for automation.
"""

import logging
import pyautogui


class ScanEngine:
    """Provides color detection and scanning capabilities for automation."""

    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.tolerance = 5  # Default color tolerance
