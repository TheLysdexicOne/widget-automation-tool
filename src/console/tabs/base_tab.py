"""
Base tab class for debug console tabs.
"""

from abc import ABC, abstractmethod
from PyQt6.QtWidgets import QWidget
from PyQt6.QtCore import QTimer
import logging


class BaseTabMeta(type(QWidget), type(ABC)):
    """Metaclass to resolve the metaclass conflict between QWidget and ABC."""

    pass


class BaseTab(QWidget, ABC, metaclass=BaseTabMeta):
    """Base class for debug console tabs."""

    def __init__(self, app, parent=None):
        super().__init__(parent)
        self.app = app
        self.logger = logging.getLogger(self.__class__.__name__)

        # Setup UI
        self._setup_ui()

        # Setup periodic updates if needed
        self._setup_updates()

    @abstractmethod
    def _setup_ui(self):
        """Setup the user interface for this tab."""
        pass

    def _setup_updates(self):
        """Setup periodic updates. Override if needed."""
        pass

    def on_tab_activated(self):
        """Called when this tab becomes active. Override if needed."""
        pass

    def on_tab_deactivated(self):
        """Called when this tab becomes inactive. Override if needed."""
        pass

    def cleanup(self):
        """Cleanup resources when tab is destroyed. Override if needed."""
        pass
