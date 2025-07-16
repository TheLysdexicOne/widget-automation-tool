"""
Custom log handler for debug console.
"""

import logging
from PyQt6.QtCore import pyqtSignal, QObject


class LogHandler(logging.Handler):
    """Custom log handler that emits signals for GUI updates."""

    def __init__(self, signal):
        super().__init__()
        self.signal = signal

    def emit(self, record):
        """Emit log record through signal."""
        try:
            msg = self.format(record)
            self.signal.emit(record.levelno, msg, record)
        except Exception:
            pass
