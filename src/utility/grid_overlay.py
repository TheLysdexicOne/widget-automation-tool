"""
Grid Overlay Utility

Provides grid overlay functionality for visualizing playable areas and debug information.
"""

import logging
from typing import Dict, Any, Optional
from PyQt6.QtWidgets import QWidget
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPainter, QPen, QColor


class GridOverlayWidget(QWidget):
    """Overlay widget that shows a grid border around the playable area."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.logger = logging.getLogger(__name__)

        # Window properties for overlay
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)

        # Grid properties
        self.playable_coords = {}
        self.border_color = QColor(255, 0, 0, 200)  # Red border
        self.border_width = 3

        # Initially hidden
        self.hide()

        self.logger.debug("Grid overlay widget initialized")

    def update_playable_area(self, coords: Dict[str, int]):
        """Update the playable area coordinates and reposition overlay."""
        if not coords:
            self.hide()
            return

        self.playable_coords = coords.copy()

        # Position the overlay to cover the entire playable area
        self.setGeometry(
            coords["x"] - self.border_width,
            coords["y"] - self.border_width,
            coords["width"] + (2 * self.border_width),
            coords["height"] + (2 * self.border_width),
        )

        # Force repaint
        self.update()

        self.logger.debug(f"Grid overlay updated for area: {coords}")

    def show_grid(self):
        """Show the grid overlay."""
        if self.playable_coords:
            self.show()
            self.raise_()
            self.logger.debug("Grid overlay shown")

    def hide_grid(self):
        """Hide the grid overlay."""
        self.hide()
        self.logger.debug("Grid overlay hidden")

    def paintEvent(self, event):
        """Paint the grid border around the playable area."""
        if not self.playable_coords:
            return

        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Set up pen for border
        pen = QPen(self.border_color, self.border_width)
        pen.setStyle(Qt.PenStyle.SolidLine)
        painter.setPen(pen)

        # Draw border rectangle
        # Coordinates are relative to this widget, so draw from border_width
        border_rect = self.rect().adjusted(
            self.border_width // 2,
            self.border_width // 2,
            -(self.border_width // 2),
            -(self.border_width // 2),
        )

        painter.drawRect(border_rect)

        # Optional: Add corner indicators for better visibility
        corner_size = 20

        # Top-left corner
        painter.drawLine(
            border_rect.topLeft().x(),
            border_rect.topLeft().y() + corner_size,
            border_rect.topLeft().x(),
            border_rect.topLeft().y(),
        )
        painter.drawLine(
            border_rect.topLeft().x(),
            border_rect.topLeft().y(),
            border_rect.topLeft().x() + corner_size,
            border_rect.topLeft().y(),
        )

        # Top-right corner
        painter.drawLine(
            border_rect.topRight().x() - corner_size,
            border_rect.topRight().y(),
            border_rect.topRight().x(),
            border_rect.topRight().y(),
        )
        painter.drawLine(
            border_rect.topRight().x(),
            border_rect.topRight().y(),
            border_rect.topRight().x(),
            border_rect.topRight().y() + corner_size,
        )

        # Bottom-left corner
        painter.drawLine(
            border_rect.bottomLeft().x(),
            border_rect.bottomLeft().y() - corner_size,
            border_rect.bottomLeft().x(),
            border_rect.bottomLeft().y(),
        )
        painter.drawLine(
            border_rect.bottomLeft().x(),
            border_rect.bottomLeft().y(),
            border_rect.bottomLeft().x() + corner_size,
            border_rect.bottomLeft().y(),
        )

        # Bottom-right corner
        painter.drawLine(
            border_rect.bottomRight().x() - corner_size,
            border_rect.bottomRight().y(),
            border_rect.bottomRight().x(),
            border_rect.bottomRight().y(),
        )
        painter.drawLine(
            border_rect.bottomRight().x(),
            border_rect.bottomRight().y() - corner_size,
            border_rect.bottomRight().x(),
            border_rect.bottomRight().y(),
        )


def create_grid_overlay(parent=None) -> GridOverlayWidget:
    """Factory function to create a grid overlay widget."""
    return GridOverlayWidget(parent)
