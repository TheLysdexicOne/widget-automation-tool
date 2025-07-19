"""
Grid Overlay Utility

Provides grid overlay functionality for visualizing playable areas and pixel art grid.
Shows the actual pixel art background grid with proper scaling using consolidated calculations.
"""

import logging
from typing import Dict, Any, Optional
from PyQt6.QtWidgets import QWidget
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPainter, QPen, QColor

from .window_utils import (
    calculate_pixel_size,
    PIXEL_ART_GRID_WIDTH,
    PIXEL_ART_GRID_HEIGHT,
)


class GridOverlayWidget(QWidget):
    """Overlay widget that shows pixel art grid and playable area border."""

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

        # Grid line properties
        self.playable_coords = {}
        self.border_color = QColor(255, 0, 0, 200)  # Red border
        self.grid_color = QColor(0, 255, 255, 100)  # Cyan grid lines
        self.border_width = 3
        self.grid_line_width = 2  # 2px wide lines as specified

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
        """Paint the pixel art grid and border around the playable area."""
        if not self.playable_coords:
            return

        painter = QPainter(self)
        painter.setRenderHint(
            QPainter.RenderHint.Antialiasing, False
        )  # Crisp pixel lines

        # Get playable area dimensions
        playable_width = self.playable_coords["width"]
        playable_height = self.playable_coords["height"]

        # Use consolidated pixel size calculation - single source of truth
        pixel_size = calculate_pixel_size(playable_width, playable_height)

        self.logger.debug(
            f"Pixel art scaling: {pixel_size:.2f}px per background pixel ({PIXEL_ART_GRID_WIDTH}x{PIXEL_ART_GRID_HEIGHT} grid)"
        )

        # Draw pixel art grid with 2px wide lines
        grid_pen = QPen(self.grid_color, self.grid_line_width)
        grid_pen.setStyle(Qt.PenStyle.SolidLine)
        painter.setPen(grid_pen)

        # Draw vertical grid lines using consolidated constants
        for i in range(PIXEL_ART_GRID_WIDTH + 1):  # +1 to include the right edge
            x = self.border_width + (i * pixel_size)
            if x <= self.width() - self.border_width:
                painter.drawLine(
                    int(x), self.border_width, int(x), self.height() - self.border_width
                )

        # Draw horizontal grid lines using consolidated constants
        for i in range(PIXEL_ART_GRID_HEIGHT + 1):  # +1 to include the bottom edge
            y = self.border_width + (i * pixel_size)
            if y <= self.height() - self.border_width:
                painter.drawLine(
                    self.border_width, int(y), self.width() - self.border_width, int(y)
                )

        # Draw playable area border on top of grid
        border_pen = QPen(self.border_color, self.border_width)
        border_pen.setStyle(Qt.PenStyle.SolidLine)
        painter.setPen(border_pen)

        # Draw border rectangle
        border_rect = self.rect().adjusted(
            self.border_width // 2,
            self.border_width // 2,
            -(self.border_width // 2),
            -(self.border_width // 2),
        )

        painter.drawRect(border_rect)

        # Add corner indicators for better visibility
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


def create_grid_overlay(parent=None) -> GridOverlayWidget:
    """Factory function to create a grid overlay widget."""
    return GridOverlayWidget(parent)
