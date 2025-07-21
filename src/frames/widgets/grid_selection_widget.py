"""
Grid Selection Widget - Region Selection Utility

Widget for selecting and editing regions with grid snapping:
- Interactive region selection
- Grid-based snapping
- Multi-region support with visual feedback

Following project standards: KISS, no duplicated calculations, modular design.
"""

from typing import Dict

from PyQt6.QtWidgets import QWidget
from PyQt6.QtCore import Qt, pyqtSignal, QRect, QPoint
from PyQt6.QtGui import QPainter, QPen, QColor, QPixmap, QBrush

from utility.window_utils import calculate_pixel_size


class GridSelectionWidget(QWidget):
    """Widget for selecting and editing regions with grid snapping."""

    region_updated = pyqtSignal(int, object)  # Emits region index and region data

    def __init__(self, screenshot: QPixmap, playable_coords: Dict, parent=None):
        super().__init__(parent)
        self.screenshot = screenshot
        self.playable_coords = playable_coords
        self.display_scale = 0.5  # Scale down for dialog display

        # Set widget size
        scaled_width = int(screenshot.width() * self.display_scale)
        scaled_height = int(screenshot.height() * self.display_scale)
        self.setFixedSize(scaled_width, scaled_height)

        self.setMouseTracking(True)

        # Multiple region boxes
        self.regions = [None, None, None]  # Up to 3 regions
        self.active_region = None  # Index of region being edited
        self.dragging = False
        self.resizing = False
        self.resize_dir = None

        # Colors for regions
        self.region_colors = [
            QColor(0, 255, 255, 120),  # Cyan
            QColor(255, 165, 0, 120),  # Orange
            QColor(0, 255, 0, 120),  # Green
        ]

    def start_region(self, idx):
        """Show region box for editing."""
        if self.regions[idx] is None:
            # Default box in center
            w, h = 60, 40
            x = (self.width() - w) // 2
            y = (self.height() - h) // 2
            self.regions[idx] = QRect(x, y, w, h)
            self.active_region = idx
            self.update()
            self.region_updated.emit(idx, self._region_to_data(self.regions[idx]))

    def remove_region(self, idx):
        """Remove region box."""
        self.regions[idx] = None
        self.active_region = None
        self.update()
        self.region_updated.emit(idx, None)

    def mousePressEvent(self, event):
        if self.active_region is not None and self.regions[self.active_region]:
            rect = self.regions[self.active_region]
            margin = 4
            pos = event.pos()
            # Check for resize on each edge/corner
            if abs(pos.x() - rect.left()) < margin and abs(pos.y() - rect.top()) < margin:
                self.resizing = True
                self.resize_dir = "tl"
            elif abs(pos.x() - rect.right()) < margin and abs(pos.y() - rect.top()) < margin:
                self.resizing = True
                self.resize_dir = "tr"
            elif abs(pos.x() - rect.left()) < margin and abs(pos.y() - rect.bottom()) < margin:
                self.resizing = True
                self.resize_dir = "bl"
            elif abs(pos.x() - rect.right()) < margin and abs(pos.y() - rect.bottom()) < margin:
                self.resizing = True
                self.resize_dir = "br"
            elif abs(pos.x() - rect.left()) < margin:
                self.resizing = True
                self.resize_dir = "l"
            elif abs(pos.x() - rect.right()) < margin:
                self.resizing = True
                self.resize_dir = "r"
            elif abs(pos.y() - rect.top()) < margin:
                self.resizing = True
                self.resize_dir = "t"
            elif abs(pos.y() - rect.bottom()) < margin:
                self.resizing = True
                self.resize_dir = "b"
            elif rect.contains(pos):
                self.dragging = True
                self.drag_offset = pos - rect.topLeft()
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self.active_region is not None and self.regions[self.active_region]:
            rect = self.regions[self.active_region]
            if self.dragging:
                # Move box, snap to grid
                new_top_left = self._snap_to_grid(event.pos() - self.drag_offset)
                rect.moveTopLeft(new_top_left)
                self.regions[self.active_region] = rect
                self.region_updated.emit(self.active_region, self._region_to_data(rect))
                self.update()
            elif self.resizing:
                # Resize box, snap to grid
                pos = self._snap_to_grid(event.pos())
                if self.resize_dir == "tl":
                    rect.setTopLeft(pos)
                elif self.resize_dir == "tr":
                    rect.setTopRight(pos)
                elif self.resize_dir == "bl":
                    rect.setBottomLeft(pos)
                elif self.resize_dir == "br":
                    rect.setBottomRight(pos)
                elif self.resize_dir == "l":
                    rect.setLeft(pos.x())
                elif self.resize_dir == "r":
                    rect.setRight(pos.x())
                elif self.resize_dir == "t":
                    rect.setTop(pos.y())
                elif self.resize_dir == "b":
                    rect.setBottom(pos.y())
                self.regions[self.active_region] = rect
                self.region_updated.emit(self.active_region, self._region_to_data(rect))
                self.update()
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        self.dragging = False
        self.resizing = False
        self.resize_dir = None
        super().mouseReleaseEvent(event)

    def _snap_to_grid(self, pos: QPoint) -> QPoint:
        orig_x = int(pos.x() / self.display_scale)
        orig_y = int(pos.y() / self.display_scale)
        pixel_size = calculate_pixel_size(self.playable_coords["width"], self.playable_coords["height"])
        if pixel_size <= 0:
            return pos
        grid_x = int(orig_x / pixel_size) * pixel_size
        grid_y = int(orig_y / pixel_size) * pixel_size
        display_x = int(grid_x * self.display_scale)
        display_y = int(grid_y * self.display_scale)
        return QPoint(display_x, display_y)

    def _region_to_data(self, rect: QRect) -> dict:
        # Convert display rect to original coordinates
        x = int(rect.x() / self.display_scale)
        y = int(rect.y() / self.display_scale)
        w = int(rect.width() / self.display_scale)
        h = int(rect.height() / self.display_scale)
        return {"x": x, "y": y, "width": w, "height": h}

    def paintEvent(self, event):
        painter = QPainter(self)
        scaled_screenshot = self.screenshot.scaled(
            self.size(),
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation,
        )
        painter.drawPixmap(0, 0, scaled_screenshot)
        # Draw region boxes
        for idx, rect in enumerate(self.regions):
            if rect:
                color = self.region_colors[idx]
                painter.setPen(QPen(color, 2))
                painter.setBrush(QBrush(color))
                painter.drawRect(rect)
