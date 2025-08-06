#!/usr/bin/env python3
"""
New QGraphicsView-based Screenshot Viewer implementation
"""

import io
import pyperclip
from typing import Dict, Optional, Callable
from PIL import Image

from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QPoint, QRectF
from PyQt6.QtGui import QPixmap, QBrush, QColor, QCursor, QPen, QWheelEvent, QMouseEvent, QKeyEvent
from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QLabel,
    QGraphicsView,
    QGraphicsScene,
    QGraphicsPixmapItem,
    QGraphicsItemGroup,
    QGraphicsLineItem,
    QFrame,
)


class ScreenshotPhotoViewer(QGraphicsView):
    """QGraphicsView-based image viewer with panning and zooming."""

    coordinatesChanged = pyqtSignal(QPoint)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._zoom = 0
        self._empty = True
        self._scene = QGraphicsScene(self)
        self._photo = QGraphicsPixmapItem()
        self._photo.setShapeMode(QGraphicsPixmapItem.ShapeMode.BoundingRectShape)
        self._scene.addItem(self._photo)
        self.setScene(self._scene)
        self.setTransformationAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)
        self.setResizeAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setBackgroundBrush(QBrush(QColor(30, 30, 30)))
        self.setFrameShape(QFrame.Shape.NoFrame)
        self.setDragMode(QGraphicsView.DragMode.ScrollHandDrag)

        # Grid overlay
        self.show_grid = False
        self._grid_item = None

        # Copy callback
        self._copy_callback: Optional[Callable] = None

    def hasPhoto(self):
        return not self._empty

    def resetView(self, scale=1):
        rect = QRectF(self._photo.pixmap().rect())
        if not rect.isNull():
            # Set scene rect larger than the image to allow overpanning
            overpan_pixels = 75
            expanded_rect = rect.adjusted(-overpan_pixels, -overpan_pixels, overpan_pixels, overpan_pixels)
            self.setSceneRect(expanded_rect)

            if (scale := max(1, scale)) == 1:
                self._zoom = 0
            if self.hasPhoto():
                unity = self.transform().mapRect(QRectF(0, 0, 1, 1))
                self.scale(1 / unity.width(), 1 / unity.height())
                viewport = self.viewport()
                if viewport:
                    viewrect = viewport.rect()
                    scenerect = self.transform().mapRect(rect)  # Use original rect, not expanded
                    factor = min(viewrect.width() / scenerect.width(), viewrect.height() / scenerect.height()) * scale
                    self.scale(factor, factor)
                    self.centerOn(self._photo)
                    self.updateCoordinates()

    def setPhoto(self, pixmap=None):
        if pixmap and not pixmap.isNull():
            self._empty = False
            self.setDragMode(QGraphicsView.DragMode.ScrollHandDrag)
            self._photo.setPixmap(pixmap)

            # Set scene rect to allow overpanning from the start
            rect = QRectF(pixmap.rect())
            overpan_pixels = 75
            expanded_rect = rect.adjusted(-overpan_pixels, -overpan_pixels, overpan_pixels, overpan_pixels)
            self.setSceneRect(expanded_rect)
        else:
            self._empty = True
            self.setDragMode(QGraphicsView.DragMode.NoDrag)
            self._photo.setPixmap(QPixmap())
        self._zoom = 0
        self.resetView()

    def zoom(self, step):
        scale_factor = 1.25
        zoom = max(0, self._zoom + (step := int(step)))
        if zoom != self._zoom:
            self._zoom = zoom
            if self._zoom > 0:
                if step > 0:
                    factor = scale_factor**step
                else:
                    factor = 1 / scale_factor ** abs(step)
                self.scale(factor, factor)
            else:
                self.resetView()
            self._update_grid()

    def wheelEvent(self, event: QWheelEvent):
        if self.hasPhoto():
            delta = event.angleDelta().y()
            self.zoom(delta and delta // abs(delta))

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if self.hasPhoto():
            self.resetView()

    def updateCoordinates(self, pos=None):
        if self._photo.isUnderMouse():
            if pos is None:
                pos = self.mapFromGlobal(QCursor.pos())
            point = self.mapToScene(pos).toPoint()
        else:
            point = QPoint()
        self.coordinatesChanged.emit(point)

    def mouseMoveEvent(self, event: QMouseEvent):
        self.updateCoordinates(event.position().toPoint())
        super().mouseMoveEvent(event)

    def mousePressEvent(self, event: QMouseEvent):
        if event.button() == Qt.MouseButton.RightButton:
            # Toggle grid
            self.show_grid = not self.show_grid
            self._update_grid()
        else:
            super().mousePressEvent(event)

    def mouseReleaseEvent(self, event: QMouseEvent):
        if event.button() == Qt.MouseButton.LeftButton:
            # Copy coordinates on left click
            if self._photo.isUnderMouse() and self._copy_callback:
                pos = event.position().toPoint()
                scene_pos = self.mapToScene(pos)
                self._copy_callback(scene_pos)
        super().mouseReleaseEvent(event)

    def leaveEvent(self, event):
        self.coordinatesChanged.emit(QPoint())
        super().leaveEvent(event)

    def keyPressEvent(self, event: QKeyEvent):
        if event.key() == Qt.Key.Key_F:
            # F key to reset to fit
            self.resetView()
        else:
            super().keyPressEvent(event)

    def _update_grid(self):
        # Remove existing grid
        if self._grid_item:
            self._scene.removeItem(self._grid_item)
            self._grid_item = None

        if self.show_grid and self.hasPhoto():
            # Create grid that shows actual pixel boundaries
            pixmap = self._photo.pixmap()
            if not pixmap.isNull():
                # Get current zoom level to determine if we should show grid
                transform = self.transform()
                scale_factor = transform.m11()  # Get current scale

                # Only show grid when zoomed in enough (when pixels are at least 8 screen pixels)
                if scale_factor >= 8.0:
                    # Create grid lines that represent actual pixel boundaries
                    grid_item = self._create_pixel_grid(pixmap.width(), pixmap.height())
                    if grid_item:
                        self._grid_item = grid_item
                        self._scene.addItem(self._grid_item)

    def _create_pixel_grid(self, width, height):
        """Create a grid that shows actual pixel boundaries."""
        # Create a group to hold all grid lines
        grid_group = QGraphicsItemGroup()

        # Create pen for grid lines - semi-transparent cyan
        pen = QPen(QColor(0, 255, 255, 100))  # Cyan with transparency
        pen.setWidth(0)  # Cosmetic pen - always 1 pixel wide regardless of zoom
        pen.setCosmetic(True)  # Important: makes lines stay same width when zoomed

        # Vertical lines - one for each pixel column
        for x in range(width + 1):  # +1 to include right border
            line = QGraphicsLineItem(x, 0, x, height)
            line.setPen(pen)
            grid_group.addToGroup(line)

        # Horizontal lines - one for each pixel row
        for y in range(height + 1):  # +1 to include bottom border
            line = QGraphicsLineItem(0, y, width, y)
            line.setPen(pen)
            grid_group.addToGroup(line)

        # Position the grid to align with the photo
        grid_group.setPos(self._photo.pos())

        return grid_group


class ScreenshotViewer(QWidget):
    """Advanced screenshot viewer with zoom, pan, grid, and click coordinates."""

    def __init__(self, frame_area: Dict, screenshot: Image.Image):
        super().__init__()
        self.frame_area = frame_area
        self.screenshot = screenshot

        # Convert PIL Image to QPixmap
        self.original_pixmap = self._pil_to_qpixmap(screenshot)

        self._setup_window()
        self._setup_ui()

    def _pil_to_qpixmap(self, pil_image: Image.Image) -> QPixmap:
        """Convert PIL Image to QPixmap."""
        # Convert PIL image to bytes
        buffer = io.BytesIO()
        pil_image.save(buffer, format="PNG")
        buffer.seek(0)

        # Load into QPixmap
        pixmap = QPixmap()
        pixmap.loadFromData(buffer.getvalue())
        return pixmap

    def _setup_window(self):
        """Setup window properties."""
        self.setWindowTitle("Frame Screenshot Viewer")
        self.setWindowFlags(Qt.WindowType.Window)
        self.resize(1280, 720)
        self.setMinimumSize(800, 600)

        # Dark theme
        self.setStyleSheet("""
            QWidget {
                background-color: #1e1e1e;
                color: #ffffff;
            }
        """)

    def _setup_ui(self):
        """Setup user interface."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Info banner (fixed 32px height)
        self.info_banner = QLabel()
        self.info_banner.setFixedHeight(32)
        self.info_banner.setStyleSheet("""
            QLabel {
                background-color: #2d2d2d;
                color: #ffffff;
                padding: 6px 10px;
                border-bottom: 1px solid #555555;
                font-family: 'Courier New', monospace;
                font-size: 10pt;
            }
        """)
        self._update_info_banner()

        # Photo viewer
        self.photo_viewer = ScreenshotPhotoViewer(self)
        self.photo_viewer.coordinatesChanged.connect(self._on_coordinates_changed)
        self.photo_viewer.setPhoto(self.original_pixmap)

        # Set copy callback
        self.photo_viewer._copy_callback = self._copy_percentage_at_position

        layout.addWidget(self.info_banner)
        layout.addWidget(self.photo_viewer)

        # Enable keyboard focus
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)

    def _update_info_banner(self):
        """Update the information banner."""
        frame_info = f"Frame: {self.frame_area.get('x', 0)}, {self.frame_area.get('y', 0)} | "
        frame_info += f"Size: {self.frame_area.get('width', 0)}x{self.frame_area.get('height', 0)} | "
        frame_info += f"Zoom: {self.photo_viewer._zoom}x | "
        frame_info += f"Grid: {'ON' if self.photo_viewer.show_grid else 'OFF'} | "
        frame_info += "Mouse: Wheel=Zoom, Drag=Pan, Right=Grid, Left=Copy%, F=Fit"
        self.info_banner.setText(frame_info)

    def _on_coordinates_changed(self, point):
        """Handle coordinate changes from photo viewer."""
        # Update info banner when coordinates change
        if not point.isNull():
            # Show current pixel coordinates in the info banner
            frame_info = f"Frame: {self.frame_area.get('x', 0)}, {self.frame_area.get('y', 0)} | "
            frame_info += f"Size: {self.frame_area.get('width', 0)}x{self.frame_area.get('height', 0)} | "
            frame_info += f"Zoom: {self.photo_viewer._zoom}x | "
            frame_info += f"Grid: {'ON' if self.photo_viewer.show_grid else 'OFF'} | "
            frame_info += f"Pixel: {point.x()}, {point.y()}"
            self.info_banner.setText(frame_info)
        else:
            self._update_info_banner()

    def _copy_percentage_at_position(self, scene_pos):
        """Copy percentage coordinates at scene position."""
        # Convert scene coordinates to percentage
        frame_width = self.frame_area.get("width", 1)
        frame_height = self.frame_area.get("height", 1)

        x_percent = max(0, min(100, (scene_pos.x() / frame_width) * 100))
        y_percent = max(0, min(100, (scene_pos.y() / frame_height) * 100))

        # Format with 6 decimal precision and copy
        percentage_text = f"{x_percent / 100:.6f}, {y_percent / 100:.6f}"
        pyperclip.copy(percentage_text)

        # Update banner to show what was copied
        self.info_banner.setText(f"Copied: {percentage_text}")
        QTimer.singleShot(2000, lambda: self._update_info_banner())

    def keyPressEvent(self, event: QKeyEvent):
        """Handle keyboard shortcuts."""
        if event.key() == Qt.Key.Key_F:
            # F key to reset to zoom-to-fit
            self.photo_viewer.resetView()
            self._update_info_banner()
        else:
            super().keyPressEvent(event)
