"""
Base tab class for debug console tabs.
"""

from abc import ABC, abstractmethod
import logging
from PyQt6.QtWidgets import QWidget


class BaseTab(QWidget):
    """Base class for debug console tabs."""

    def __init__(self, app, debug_console=None):
        super().__init__()
        self.app = app
        self.debug_console = debug_console  # Store reference to debug console
        self.logger = logging.getLogger(self.__class__.__name__)
        self._setup_ui()

    @abstractmethod
    def _setup_ui(self):
        """Setup the tab UI - must be implemented by subclasses."""
        pass
