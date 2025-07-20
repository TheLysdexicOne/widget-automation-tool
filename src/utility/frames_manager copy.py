"""
Frames Management System

Handles frame (scene/minigame) detection and management:
- Frame creation with screenshots and metadata
- Region selection with pixel art grid snapping
- Frame database management (JSON-based)
- Screenshot management and storage

Following project standards: KISS, no duplicated calculations, modular design.
"""

import logging
import json
import uuid
import time
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple

try:
    import win32gui
    from PIL import Image, ImageGrab

    WIN32_AVAILABLE = True
except ImportError:
    WIN32_AVAILABLE = False

from PyQt6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QFormLayout,
    QGridLayout,
    QLabel,
    QLineEdit,
    QCheckBox,
    QPushButton,
    QListWidget,
    QListWidgetItem,
    QScrollArea,
    QSizePolicy,
    QFrame,
    QDialogButtonBox,
    QMessageBox,
    QWidget,
    QTextEdit,
    QApplication,
    QMenu,
)
from PyQt6.QtCore import Qt, pyqtSignal, QRect, QPoint
from PyQt6.QtGui import QPainter, QPen, QColor, QPixmap, QFont, QBrush

from utility.window_utils import (
    calculate_pixel_art_grid_position,
    calculate_pixel_size,
    PIXEL_ART_GRID_WIDTH,
    PIXEL_ART_GRID_HEIGHT,
)

logger = logging.getLogger(__name__)


class FramesManager:
    """Manages frame data and screenshot storage."""

    def __init__(self, base_path: Path):
        self.base_path = base_path
        self.frames_db_path = base_path / "frames" / "frames_database.json"
        self.screenshots_dir = base_path / "assets" / "screenshots"

        # Ensure directories exist
        self.frames_db_path.parent.mkdir(parents=True, exist_ok=True)
        self.screenshots_dir.mkdir(parents=True, exist_ok=True)

        self.frames_data = self._load_frames_database()

    def _load_frames_database(self) -> Dict:
        """Load frames database from JSON file."""
        if self.frames_db_path.exists():
            try:
                with open(self.frames_db_path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Error loading frames database: {e}")

        # Return default structure
        return {"frames": []}

    def _save_frames_database(self) -> bool:
        """Save frames database to JSON file."""
        try:
            # Create backup first
            if self.frames_db_path.exists():
                backup_path = self.frames_db_path.with_suffix(".json.backup")
                import shutil

                shutil.copy2(self.frames_db_path, backup_path)

            with open(self.frames_db_path, "w", encoding="utf-8") as f:
                json.dump(self.frames_data, f, indent=2, ensure_ascii=False)
            return True
        except Exception as e:
            logger.error(f"Error saving frames database: {e}")
            return False

    def get_frame_list(self) -> List[Dict]:
        """Get list of all frames."""
        return self.frames_data.get("frames", [])

    def get_frame_by_name(self, name: str) -> Optional[Dict]:
        """Get frame data by name."""
        for frame in self.frames_data.get("frames", []):
            if frame.get("name") == name:
                return frame
        return None

    def save_screenshot(self, screenshot: Image.Image, frame_name: str = None) -> str:
        """Save screenshot and return UUID."""
        screenshot_uuid = str(uuid.uuid4())
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        filename = f"{timestamp}_{screenshot_uuid}.png"

        if frame_name:
            filename = f"{frame_name}_{filename}"

        screenshot_path = self.screenshots_dir / filename
        screenshot.save(screenshot_path)
        logger.info(f"Screenshot saved: {screenshot_path}")
        return screenshot_uuid

    def add_frame(self, frame_data: Dict) -> bool:
        """Add new frame to database."""
        try:
            self.frames_data["frames"].append(frame_data)
            return self._save_frames_database()
        except Exception as e:
            logger.error(f"Error adding frame: {e}")
            return False

    def update_frame(self, frame_name: str, frame_data: Dict) -> bool:
        """Update existing frame in database."""
        try:
            for i, frame in enumerate(self.frames_data["frames"]):
                if frame.get("name") == frame_name:
                    self.frames_data["frames"][i] = frame_data
                    return self._save_frames_database()
            return False
        except Exception as e:
            logger.error(f"Error updating frame: {e}")
            return False

    def delete_screenshot(self, screenshot_uuid: str) -> bool:
        """Delete screenshot file."""
        try:
            # Find and delete the file
            for screenshot_file in self.screenshots_dir.glob(f"*{screenshot_uuid}*"):
                screenshot_file.unlink()
                logger.info(f"Deleted screenshot: {screenshot_file}")
                return True
            return False
        except Exception as e:
            logger.error(f"Error deleting screenshot: {e}")
            return False


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
            if (
                abs(pos.x() - rect.left()) < margin
                and abs(pos.y() - rect.top()) < margin
            ):
                self.resizing = True
                self.resize_dir = "tl"
            elif (
                abs(pos.x() - rect.right()) < margin
                and abs(pos.y() - rect.top()) < margin
            ):
                self.resizing = True
                self.resize_dir = "tr"
            elif (
                abs(pos.x() - rect.left()) < margin
                and abs(pos.y() - rect.bottom()) < margin
            ):
                self.resizing = True
                self.resize_dir = "bl"
            elif (
                abs(pos.x() - rect.right()) < margin
                and abs(pos.y() - rect.bottom()) < margin
            ):
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
        pixel_size = calculate_pixel_size(
            self.playable_coords["width"], self.playable_coords["height"]
        )
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


class AddFrameDialog(QDialog):
    """Dialog for adding new frame with screenshot and regions."""

    def __init__(self, screenshot: QPixmap, playable_coords: Dict, parent=None):
        super().__init__(parent)
        self.screenshot = screenshot
        self.playable_coords = playable_coords
        self.regions = []

        self.setWindowTitle("Add New Frame")
        self.setModal(True)
        self.resize(800, 600)

        self._setup_ui()

    def _setup_ui(self):
        """Setup the dialog UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 10, 20, 10)  # Dialog padding

        # Form section
        form_layout = QFormLayout()

        # Item and Frame fields
        item_frame_layout = QHBoxLayout()
        self.item_edit = QLineEdit()
        self.frame_edit = QLineEdit()
        item_frame_layout.addWidget(QLabel("Item:"))
        item_frame_layout.addWidget(self.item_edit)
        item_frame_layout.addWidget(QLabel("Frame:"))
        item_frame_layout.addWidget(self.frame_edit)

        # Can be automated checkbox
        self.automation_checkbox = QCheckBox("Can be automated")

        form_layout.addRow(item_frame_layout)
        form_layout.addRow(self.automation_checkbox)

        # Screenshot in a centered box (create grid_widget first!)
        screenshot_box = QHBoxLayout()
        screenshot_box.setAlignment(Qt.AlignmentFlag.AlignHCenter)

        self.grid_widget = GridSelectionWidget(self.screenshot, self.playable_coords)
        self.grid_widget.region_updated.connect(self._on_region_updated)
        self.grid_widget.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding
        )
        screenshot_box.addWidget(self.grid_widget)

        # Text regions section
        regions_label = QLabel("Text Regions:")
        regions_label.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
        form_layout.addRow(regions_label)

        self.regions_layout = QVBoxLayout()
        self._add_region_row()  # <-- Now safe to call
        form_layout.addRow(self.regions_layout)

        layout.addLayout(form_layout)

        # Spacer for padding between text/regions and screenshot
        spacer = QWidget()
        spacer.setFixedHeight(16)
        layout.addWidget(spacer)
        layout.addLayout(screenshot_box)

        # Consistent Cancel/Save buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        cancel_button = QPushButton("Cancel")
        cancel_button.clicked.connect(self.reject)
        save_button = QPushButton("Save")
        save_button.clicked.connect(self.accept)
        button_layout.addWidget(cancel_button)
        button_layout.addWidget(save_button)
        layout.addLayout(button_layout)

    def _add_region_row(self):
        """Add a new text region row with + / - toggle."""
        row_layout = QHBoxLayout()

        text_edit = QLineEdit()
        text_edit.setPlaceholderText("Enter text description")

        idx = len(self.regions)
        toggle_button = QPushButton("+")
        toggle_button.setFixedSize(30, 30)

        coord_label = QLabel("No region selected")
        coord_label.setMinimumWidth(150)

        def on_toggle():
            if toggle_button.text() == "+":
                self.grid_widget.start_region(idx)
                toggle_button.setText("-")
            else:
                self.grid_widget.remove_region(idx)
                toggle_button.setText("+")
                coord_label.setText("No region selected")

        toggle_button.clicked.connect(on_toggle)

        def on_region_updated(region_idx, region):
            if region_idx == idx and region:
                coord_label.setText(
                    f"({region['x']}, {region['y']}) {region['width']}x{region['height']}"
                )
                self.regions[region_idx]["region"] = region
            elif region_idx == idx and region is None:
                coord_label.setText("No region selected")
                self.regions[region_idx]["region"] = None

        self.grid_widget.region_updated.connect(on_region_updated)

        row_layout.addWidget(QLabel("Text:"))
        row_layout.addWidget(text_edit)
        row_layout.addWidget(QLabel("Region:"))
        row_layout.addWidget(toggle_button)
        row_layout.addWidget(coord_label)

        region_data = {
            "text_edit": text_edit,
            "coord_label": coord_label,
            "region": None,
        }
        self.regions.append(region_data)
        self.regions_layout.addLayout(row_layout)

        # Add another row if this isn't the third one yet
        if len(self.regions) < 3:
            self._add_region_row()

    def _on_region_updated(self, region: Dict):
        """Handle region selection completion."""
        if hasattr(self, "current_region_index") and self.current_region_index < len(
            self.regions
        ):
            region_data = self.regions[self.current_region_index]
            region_data["region"] = region
            region_data["coord_label"].setText(
                f"({region['x']}, {region['y']}) {region['width']}x{region['height']}"
            )

    def get_frame_data(self) -> Dict:
        """Get frame data from dialog."""
        text_regions = []
        for region_data in self.regions:
            text = region_data["text_edit"].text().strip()
            if text and region_data["region"]:
                text_regions.append({"text": text, "region": region_data["region"]})

        return {
            "name": self.frame_edit.text().strip(),
            "item": self.item_edit.text().strip(),
            "automation": 1 if self.automation_checkbox.isChecked() else 0,
            "text": text_regions,
            "screenshots": [],  # Will be added by the manager
        }


class AttachToFrameDialog(QDialog):
    """Dialog for attaching screenshot to existing frame."""

    def __init__(self, screenshot: QPixmap, frames_list: List[Dict], parent=None):
        super().__init__(parent)
        self.screenshot = screenshot
        self.frames_list = frames_list
        self.selected_frame = None

        self.setWindowTitle("Attach to Frame")
        self.setModal(True)
        self.resize(600, 500)

        self._setup_ui()

    def _setup_ui(self):
        """Setup the attach dialog UI."""
        layout = QHBoxLayout(self)

        # Left side - Frame list
        left_layout = QVBoxLayout()
        left_layout.addWidget(QLabel("Select Frame:"))

        self.frames_list_widget = QListWidget()
        self.frames_list_widget.itemClicked.connect(self._on_frame_selected)

        # Populate frame list
        for frame in self.frames_list:
            item = QListWidgetItem(
                f"{frame.get('item', 'Unknown')} - {frame.get('name', 'Unnamed')}"
            )
            item.setData(Qt.ItemDataRole.UserRole, frame)
            self.frames_list_widget.addItem(item)

        left_layout.addWidget(self.frames_list_widget)

        # Consistent Cancel/Save buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.clicked.connect(self.reject)
        self.save_button = QPushButton("Save")
        self.save_button.setEnabled(False)
        self.save_button.clicked.connect(self.accept)
        button_layout.addWidget(self.cancel_button)
        button_layout.addWidget(self.save_button)
        left_layout.addLayout(button_layout)

        # Right side - Screenshot preview
        right_layout = QVBoxLayout()
        right_layout.addWidget(QLabel("Screenshot Preview:"))

        # Screenshot display
        screenshot_label = QLabel()
        scaled_screenshot = self.screenshot.scaled(
            250,
            200,
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation,
        )
        screenshot_label.setPixmap(scaled_screenshot)
        screenshot_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        screenshot_label.setFrameStyle(QFrame.Shape.Box)

        right_layout.addWidget(screenshot_label)
        right_layout.addStretch()

        # Add layouts to main layout
        layout.addLayout(left_layout, 2)
        layout.addLayout(right_layout, 1)

    def _on_frame_selected(self, item: QListWidgetItem):
        """Handle frame selection."""
        self.selected_frame = item.data(Qt.ItemDataRole.UserRole)
        self.save_button.setEnabled(True)

    def get_selected_frame(self) -> Optional[Dict]:
        """Get the selected frame data."""
        return self.selected_frame


class ScreenshotGalleryWidget(QWidget):
    """Widget for displaying screenshot gallery with delete functionality."""

    screenshot_deleted = pyqtSignal(str)  # Emits UUID of deleted screenshot
    screenshot_clicked = pyqtSignal(str)  # Emits UUID of clicked screenshot

    def __init__(self, screenshots: List[str], screenshots_dir: Path, parent=None):
        super().__init__(parent)
        self.screenshots = screenshots
        self.screenshots_dir = screenshots_dir
        self.marked_for_deletion = set()

        self._setup_ui()

    def _setup_ui(self):
        """Setup gallery UI."""
        layout = QGridLayout(self)

        # Display screenshots in a grid
        row, col = 0, 0
        max_cols = 3

        for screenshot_uuid in self.screenshots:
            screenshot_widget = self._create_screenshot_widget(screenshot_uuid)
            layout.addWidget(screenshot_widget, row, col)

            col += 1
            if col >= max_cols:
                col = 0
                row += 1

        if not self.screenshots:
            no_screenshots_label = QLabel("No screenshots available")
            no_screenshots_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            layout.addWidget(no_screenshots_label, 0, 0)

    def _create_screenshot_widget(self, screenshot_uuid: str) -> QWidget:
        """Create widget for individual screenshot."""
        widget = QFrame()
        widget.setFrameStyle(QFrame.Shape.Box)
        widget.setMaximumSize(120, 100)

        layout = QVBoxLayout(widget)
        layout.setContentsMargins(5, 5, 5, 5)

        # Find screenshot file
        screenshot_path = None
        for file_path in self.screenshots_dir.glob(f"*{screenshot_uuid}*"):
            screenshot_path = file_path
            break

        # Screenshot thumbnail
        if screenshot_path and screenshot_path.exists():
            pixmap = QPixmap(str(screenshot_path))
            thumbnail = pixmap.scaled(
                80,
                60,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation,
            )

            screenshot_label = QLabel()
            screenshot_label.setPixmap(thumbnail)
            screenshot_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            screenshot_label.mousePressEvent = (
                lambda e, uuid=screenshot_uuid: self._on_screenshot_clicked(uuid)
            )
            layout.addWidget(screenshot_label)
        else:
            # Missing file placeholder
            placeholder = QLabel("Missing\nFile")
            placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
            placeholder.setStyleSheet("color: red;")
            layout.addWidget(placeholder)

        # Delete button (X)
        delete_button = QPushButton("×")
        delete_button.setMaximumSize(20, 20)
        delete_button.setStyleSheet(
            """
            QPushButton {
                background-color: red;
                color: white;
                border: none;
                border-radius: 10px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: darkred;
            }
        """
        )
        delete_button.clicked.connect(
            lambda: self._on_delete_clicked(screenshot_uuid, widget)
        )

        # Position delete button in top-right corner
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        button_layout.addWidget(delete_button)
        layout.insertLayout(0, button_layout)

        return widget

    def _on_screenshot_clicked(self, screenshot_uuid: str):
        """Handle screenshot thumbnail click."""
        self.screenshot_clicked.emit(screenshot_uuid)

    def _on_delete_clicked(self, screenshot_uuid: str, widget: QWidget):
        """Handle delete button click."""
        if screenshot_uuid in self.marked_for_deletion:
            # Unmark for deletion
            self.marked_for_deletion.remove(screenshot_uuid)
            widget.setStyleSheet("")
        else:
            # Mark for deletion
            self.marked_for_deletion.add(screenshot_uuid)
            widget.setStyleSheet("background-color: rgba(255, 0, 0, 50);")

    def get_screenshots_to_delete(self) -> List[str]:
        """Get list of screenshot UUIDs marked for deletion."""
        return list(self.marked_for_deletion)


class EditFramesDialog(QDialog):
    """Dialog for editing existing frames."""

    def __init__(self, frames_list: List[Dict], screenshots_dir: Path, parent=None):
        super().__init__(parent)
        self.frames_list = frames_list
        self.screenshots_dir = screenshots_dir
        self.selected_frame = None
        self.modified_frame_data = None
        self.screenshots_to_delete = []

        self.setWindowTitle("Edit Frames")
        self.setModal(True)
        self.resize(900, 700)

        self._setup_ui()

    def _setup_ui(self):
        """Setup the edit frames dialog UI."""
        layout = QHBoxLayout(self)

        # Left side - Frame list
        left_layout = QVBoxLayout()
        left_layout.addWidget(QLabel("Select Frame to Edit:"))

        self.frames_list_widget = QListWidget()
        self.frames_list_widget.itemClicked.connect(self._on_frame_selected)
        self.frames_list_widget.setMaximumWidth(200)

        # Populate frame list
        for frame in self.frames_list:
            frame_name = frame.get("name", "Unnamed")
            item_name = frame.get("item", "Unknown")
            item = QListWidgetItem(f"{frame_name} ({item_name})")
            item.setData(Qt.ItemDataRole.UserRole, frame)
            self.frames_list_widget.addItem(item)

        left_layout.addWidget(self.frames_list_widget)

        # Center - Frame editing form
        center_layout = QVBoxLayout()

        # Form section
        form_layout = QFormLayout()

        # Item and Frame fields
        item_frame_layout = QHBoxLayout()
        self.item_edit = QLineEdit()
        self.frame_edit = QLineEdit()
        item_frame_layout.addWidget(QLabel("Item:"))
        item_frame_layout.addWidget(self.item_edit)
        item_frame_layout.addWidget(QLabel("Frame:"))
        item_frame_layout.addWidget(self.frame_edit)

        # Can be automated checkbox
        self.automation_checkbox = QCheckBox("Can be automated")

        form_layout.addRow(item_frame_layout)
        form_layout.addRow(self.automation_checkbox)

        # Text regions section
        regions_label = QLabel("Text Regions:")
        regions_label.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
        form_layout.addRow(regions_label)

        self.regions_layout = QVBoxLayout()
        self._setup_empty_regions()
        form_layout.addRow(self.regions_layout)

        center_layout.addLayout(form_layout)
        center_layout.addStretch()

        # Right side - Screenshots gallery
        right_layout = QVBoxLayout()

        # Screenshots header with toggle button
        screenshots_header = QHBoxLayout()
        screenshots_header.addWidget(QLabel("SCREENSHOTS"))

        self.images_button = QPushButton("images>")
        self.images_button.clicked.connect(self._toggle_screenshots)
        self.images_button.setMaximumWidth(60)
        screenshots_header.addWidget(self.images_button)

        right_layout.addLayout(screenshots_header)

        # Screenshots scroll area (initially hidden)
        self.screenshots_scroll = QScrollArea()
        self.screenshots_scroll.setWidgetResizable(True)
        self.screenshots_scroll.setMaximumWidth(400)
        self.screenshots_scroll.hide()  # Initially hidden

        self.screenshots_widget = None
        right_layout.addWidget(self.screenshots_scroll)

        # Consistent Cancel/Save buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.clicked.connect(self.reject)
        self.save_button = QPushButton("Save")
        self.save_button.clicked.connect(self._save_changes)
        self.save_button.setEnabled(False)
        button_layout.addWidget(self.cancel_button)
        button_layout.addWidget(self.save_button)
        center_layout.addLayout(button_layout)

        # Add all layouts
        layout.addLayout(left_layout, 1)
        layout.addLayout(center_layout, 2)
        layout.addLayout(right_layout, 2)

        # Initially disable editing
        self._set_editing_enabled(False)

    def _setup_empty_regions(self):
        """Setup empty text regions for editing."""
        self.regions = []
        for i in range(3):
            self._add_region_row()

    def _add_region_row(self):
        """Add a text region row."""
        row_layout = QHBoxLayout()

        text_edit = QLineEdit()
        text_edit.setPlaceholderText("Enter text description")

        coord_label = QLabel("No region selected")
        coord_label.setMinimumWidth(150)

        row_layout.addWidget(QLabel("Text:"))
        row_layout.addWidget(text_edit)
        row_layout.addWidget(QLabel("Region:"))
        row_layout.addWidget(coord_label)

        # Store references
        region_data = {
            "text_edit": text_edit,
            "coord_label": coord_label,
            "region": None,
        }
        self.regions.append(region_data)
        self.regions_layout.addLayout(row_layout)

    def _on_frame_selected(self, item: QListWidgetItem):
        """Handle frame selection from list."""
        self.selected_frame = item.data(Qt.ItemDataRole.UserRole)
        self._load_frame_data(self.selected_frame)
        self._set_editing_enabled(True)
        self.save_button.setEnabled(True)

        # Update screenshots gallery
        self._update_screenshots_gallery()

    def _load_frame_data(self, frame_data: Dict):
        """Load frame data into editing form."""
        # Load basic fields
        self.item_edit.setText(frame_data.get("item", ""))
        self.frame_edit.setText(frame_data.get("name", ""))
        self.automation_checkbox.setChecked(frame_data.get("automation", 0) == 1)

        # Load text regions
        text_regions = frame_data.get("text", [])
        for i, region_data in enumerate(self.regions):
            if i < len(text_regions):
                text_region = text_regions[i]
                region_data["text_edit"].setText(text_region.get("text", ""))
                region_data["region"] = text_region.get("region")

                if region_data["region"]:
                    region = region_data["region"]
                    region_data["coord_label"].setText(
                        f"({region['x']}, {region['y']}) {region['width']}x{region['height']}"
                    )
                else:
                    region_data["coord_label"].setText("No region selected")
            else:
                # Clear unused regions
                region_data["text_edit"].setText("")
                region_data["coord_label"].setText("No region selected")
                region_data["region"] = None

    def _set_editing_enabled(self, enabled: bool):
        """Enable or disable editing controls."""
        self.item_edit.setEnabled(enabled)
        self.frame_edit.setEnabled(enabled)
        self.automation_checkbox.setEnabled(enabled)

        for region_data in self.regions:
            region_data["text_edit"].setEnabled(enabled)

    def _toggle_screenshots(self):
        """Toggle screenshots gallery visibility."""
        if self.screenshots_scroll.isVisible():
            self.screenshots_scroll.hide()
            self.images_button.setText("images>")
        else:
            self.screenshots_scroll.show()
            self.images_button.setText("images<")

    def _update_screenshots_gallery(self):
        """Update screenshots gallery for selected frame."""
        if not self.selected_frame:
            return

        screenshots = self.selected_frame.get("screenshots", [])
        self.screenshots_widget = ScreenshotGalleryWidget(
            screenshots, self.screenshots_dir, self
        )
        self.screenshots_widget.screenshot_clicked.connect(self._show_screenshot_popup)

        self.screenshots_scroll.setWidget(self.screenshots_widget)

    def _show_screenshot_popup(self, screenshot_uuid: str):
        """Show popup with larger screenshot view."""
        # Find screenshot file
        screenshot_path = None
        for file_path in self.screenshots_dir.glob(f"*{screenshot_uuid}*"):
            screenshot_path = file_path
            break

        if not screenshot_path or not screenshot_path.exists():
            QMessageBox.warning(self, "Error", "Screenshot file not found")
            return

        # Create popup dialog
        popup = QDialog(self)
        popup.setWindowTitle("Screenshot View")
        popup.setModal(True)

        layout = QVBoxLayout(popup)

        # Screenshot display
        screenshot_label = QLabel()
        pixmap = QPixmap(str(screenshot_path))
        scaled_pixmap = pixmap.scaled(
            600,
            400,
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation,
        )
        screenshot_label.setPixmap(scaled_pixmap)
        screenshot_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        layout.addWidget(screenshot_label)

        # Close button
        close_button = QPushButton("Close")
        close_button.clicked.connect(popup.accept)
        layout.addWidget(close_button)

        popup.exec()

    def _save_changes(self):
        """Save changes to frame data."""
        if not self.selected_frame:
            return

        # Collect modified data
        text_regions = []
        for region_data in self.regions:
            text = region_data["text_edit"].text().strip()
            if text and region_data["region"]:
                text_regions.append({"text": text, "region": region_data["region"]})

        self.modified_frame_data = {
            "name": self.frame_edit.text().strip(),
            "item": self.item_edit.text().strip(),
            "automation": 1 if self.automation_checkbox.isChecked() else 0,
            "text": text_regions,
            "screenshots": self.selected_frame.get("screenshots", []),
        }

        # Get screenshots marked for deletion
        if self.screenshots_widget:
            self.screenshots_to_delete = (
                self.screenshots_widget.get_screenshots_to_delete()
            )
            # Remove deleted screenshots from frame data
            for uuid_to_delete in self.screenshots_to_delete:
                if uuid_to_delete in self.modified_frame_data["screenshots"]:
                    self.modified_frame_data["screenshots"].remove(uuid_to_delete)

        self.accept()

    def get_modified_data(self) -> Tuple[Optional[str], Optional[Dict], List[str]]:
        """Get modified frame data and deletion list."""
        original_name = self.selected_frame.get("name") if self.selected_frame else None
        return original_name, self.modified_frame_data, self.screenshots_to_delete


class FramesMenuSystem:
    """Main system for managing frames functionality."""

    def __init__(self, parent_widget, frames_manager: FramesManager):
        self.parent = parent_widget
        self.frames_manager = frames_manager
        self.logger = logging.getLogger(__name__)

    def show_frames_menu(self):
        """Show the main FRAMES menu."""
        menu = QMenu("FRAMES", self.parent)

        # Add New Frame
        add_frame_action = menu.addAction("Add New Frame")
        add_frame_action.triggered.connect(self._show_add_frame_dialog)

        # Attach to Frame
        attach_frame_action = menu.addAction("Attach to Frame")
        attach_frame_action.triggered.connect(self._show_attach_frame_dialog)

        menu.addSeparator()

        # Edit Frames
        edit_frames_action = menu.addAction("Edit Frames")
        edit_frames_action.triggered.connect(self._show_edit_frames_dialog)

        # Position menu to not exceed application bounds
        button_pos = self.parent.frames_button.mapToGlobal(
            self.parent.frames_button.rect().bottomLeft()
        )
        menu_size = menu.sizeHint()

        # Adjust if menu would go outside parent bounds
        parent_geometry = self.parent.geometry()
        if button_pos.x() + menu_size.width() > parent_geometry.right():
            button_pos.setX(parent_geometry.right() - menu_size.width())

        menu.exec(button_pos)

    def _show_add_frame_dialog(self):
        """Show Add New Frame dialog."""
        self.logger.info("Opening Add New Frame dialog")

        # Capture screenshot
        screenshot = self._capture_playable_screenshot()
        if not screenshot:
            QMessageBox.warning(self.parent, "Error", "Failed to capture screenshot")
            return

        # Show dialog
        dialog = AddFrameDialog(screenshot, self.parent.playable_coords, self.parent)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self._save_new_frame(dialog.get_frame_data(), screenshot)

    def _show_attach_frame_dialog(self):
        """Show Attach to Frame dialog."""
        self.logger.info("Opening Attach to Frame dialog")

        # Get existing frames
        frames_list = self.frames_manager.get_frame_list()
        if not frames_list:
            QMessageBox.information(
                self.parent,
                "No Frames",
                "No frames available. Create a frame first using 'Add New Frame'.",
            )
            return

        # Capture screenshot
        screenshot = self._capture_playable_screenshot()
        if not screenshot:
            QMessageBox.warning(self.parent, "Error", "Failed to capture screenshot")
            return

        # Show dialog
        dialog = AttachToFrameDialog(screenshot, frames_list, self.parent)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            selected_frame = dialog.get_selected_frame()
            if selected_frame:
                # Convert QPixmap to PIL Image and save screenshot
                screenshot_path = Path.cwd() / "temp_attach_screenshot.png"
                screenshot.save(str(screenshot_path))
                pil_image = Image.open(screenshot_path)

                # Save screenshot and get UUID
                screenshot_uuid = self.frames_manager.save_screenshot(
                    pil_image, selected_frame.get("name", "unnamed")
                )

                # Attach to frame
                self._attach_screenshot_to_frame(
                    selected_frame.get("name"), screenshot_uuid
                )

                # Clean up temp file
                screenshot_path.unlink()

    def _show_edit_frames_dialog(self):
        """Show Edit Frames dialog."""
        self.logger.info("Opening Edit Frames dialog")

        # Get existing frames
        frames_list = self.frames_manager.get_frame_list()
        if not frames_list:
            QMessageBox.information(
                self.parent,
                "No Frames",
                "No frames available. Create a frame first using 'Add New Frame'.",
            )
            return

        # Show dialog
        dialog = EditFramesDialog(
            frames_list, self.frames_manager.screenshots_dir, self.parent
        )

        if dialog.exec() == QDialog.DialogCode.Accepted:
            frame_name, modified_data, screenshots_to_delete = (
                dialog.get_modified_data()
            )
            if frame_name and modified_data:
                self._save_frame_changes(
                    frame_name, modified_data, screenshots_to_delete
                )

    def _capture_playable_screenshot(self) -> Optional[QPixmap]:
        """Capture screenshot of playable area using window-specific capture."""
        try:
            # Get playable area coordinates
            playable = self.parent.playable_coords
            if not playable or not all(
                k in playable for k in ["x", "y", "width", "height"]
            ):
                self.logger.warning("Invalid playable coordinates, using fallback")
                return self._capture_fallback_screenshot()

            self.logger.info(f"Capturing screenshot of playable area: {playable}")

            # Method 1: Try direct coordinate capture with explicit all_screens=True
            try:
                self.logger.info(
                    "Attempting direct coordinate capture with all_screens=True"
                )
                screenshot = ImageGrab.grab(
                    bbox=(
                        playable["x"],
                        playable["y"],
                        playable["x"] + playable["width"],
                        playable["y"] + playable["height"],
                    ),
                    all_screens=True,  # Explicitly capture from all screens including negative coords
                )

                self.logger.info(f"Direct capture successful, size: {screenshot.size}")

                # Verify we got the right size
                if screenshot.size == (playable["width"], playable["height"]):
                    # Convert to QPixmap
                    screenshot_path = Path.cwd() / "temp_screenshot.png"
                    screenshot.save(screenshot_path)

                    # Verify the image has content
                    if screenshot.getbbox() is not None:
                        pixmap = QPixmap(str(screenshot_path))
                        self.logger.info(
                            f"Direct capture QPixmap size: {pixmap.width()}x{pixmap.height()}"
                        )
                        screenshot_path.unlink()  # Clean up temp file
                        return pixmap
                    else:
                        self.logger.warning("Direct capture image appears empty")
                        screenshot_path.unlink()
                else:
                    self.logger.warning(
                        f"Direct capture size mismatch: got {screenshot.size}, expected ({playable['width']}, {playable['height']})"
                    )

            except Exception as e:
                self.logger.warning(f"Direct coordinate capture failed: {e}")

            # Method 2: Window-specific capture if we have hwnd
            if WIN32_AVAILABLE and self.parent.target_hwnd:
                try:
                    self.logger.info("Attempting window-specific capture")

                    # Bring window to foreground first
                    win32gui.SetForegroundWindow(self.parent.target_hwnd)
                    import time

                    time.sleep(0.3)  # Longer delay for window activation

                    # Get window rectangle
                    window_rect = win32gui.GetWindowRect(self.parent.target_hwnd)
                    self.logger.info(f"Window rectangle: {window_rect}")

                    # Capture the entire window first
                    window_screenshot = ImageGrab.grab(
                        bbox=window_rect, all_screens=True
                    )

                    # Calculate relative coordinates within the window
                    # playable coords are absolute, window_rect gives us window position
                    rel_x = playable["x"] - window_rect[0]
                    rel_y = playable["y"] - window_rect[1]

                    self.logger.info(
                        f"Relative playable coords: ({rel_x}, {rel_y}) {playable['width']}x{playable['height']}"
                    )

                    # Crop to playable area
                    if (
                        rel_x >= 0
                        and rel_y >= 0
                        and rel_x + playable["width"] <= window_screenshot.width
                        and rel_y + playable["height"] <= window_screenshot.height
                    ):

                        playable_screenshot = window_screenshot.crop(
                            (
                                rel_x,
                                rel_y,
                                rel_x + playable["width"],
                                rel_y + playable["height"],
                            )
                        )

                        # Convert to QPixmap
                        screenshot_path = Path.cwd() / "temp_screenshot.png"
                        playable_screenshot.save(screenshot_path)

                        if playable_screenshot.getbbox() is not None:
                            pixmap = QPixmap(str(screenshot_path))
                            self.logger.info(
                                f"Window capture successful: {pixmap.width()}x{pixmap.height()}"
                            )
                            screenshot_path.unlink()
                            return pixmap
                        else:
                            screenshot_path.unlink()

                    else:
                        self.logger.warning(
                            "Playable area extends outside window bounds"
                        )

                except Exception as e:
                    self.logger.warning(f"Window-specific capture failed: {e}")

            # Fall back to full screen approach
            self.logger.warning("All capture methods failed, using fallback")
            return self._capture_fallback_screenshot()

        except Exception as e:
            self.logger.error(f"Error in screenshot capture: {e}")
            return self._capture_fallback_screenshot()

    def _capture_fallback_screenshot(self) -> Optional[QPixmap]:
        """Fallback screenshot capture of entire screen for testing."""
        try:
            self.logger.info("Using fallback screenshot capture (entire screen)")

            # Capture entire screen
            screenshot = ImageGrab.grab()

            # Scale down for dialog display
            screenshot = screenshot.resize((800, 600), Image.Resampling.LANCZOS)

            # Convert to QPixmap
            screenshot_path = Path.cwd() / "temp_fallback_screenshot.png"
            screenshot.save(screenshot_path)

            pixmap = QPixmap(str(screenshot_path))
            self.logger.info(
                f"Fallback screenshot size: {pixmap.width()}x{pixmap.height()}"
            )

            screenshot_path.unlink()  # Clean up temp file

            return pixmap

        except Exception as e:
            self.logger.error(f"Error in fallback screenshot capture: {e}")
            return None

    def _save_new_frame(self, frame_data: Dict, screenshot: QPixmap):
        """Save new frame with screenshot."""
        try:
            # Convert QPixmap to PIL Image for saving
            screenshot_path = Path.cwd() / "temp_frame_screenshot.png"
            screenshot.save(str(screenshot_path))
            pil_image = Image.open(screenshot_path)

            # Save screenshot and get UUID
            screenshot_uuid = self.frames_manager.save_screenshot(
                pil_image, frame_data["name"]
            )

            # Add screenshot UUID to frame data
            frame_data["screenshots"] = [screenshot_uuid]

            # Save frame to database
            if self.frames_manager.add_frame(frame_data):
                QMessageBox.information(
                    self.parent,
                    "Success",
                    f"Frame '{frame_data['name']}' saved successfully!",
                )
                self.logger.info(f"New frame created: {frame_data['name']}")
            else:
                QMessageBox.warning(
                    self.parent, "Error", "Failed to save frame to database"
                )

            # Clean up temp file
            screenshot_path.unlink()

        except Exception as e:
            self.logger.error(f"Error saving new frame: {e}")
            QMessageBox.warning(self.parent, "Error", f"Failed to save frame: {str(e)}")

    def _attach_screenshot_to_frame(self, frame_name: str, screenshot_uuid: str):
        """Attach screenshot to existing frame."""
        try:
            frames_data = self.frames_manager.get_frame_list()
            for frame_data in frames_data:
                if frame_data.get("name") == frame_name:
                    if "screenshots" not in frame_data:
                        frame_data["screenshots"] = []

                    if screenshot_uuid not in frame_data["screenshots"]:
                        frame_data["screenshots"].append(screenshot_uuid)

                        # Update frame in database
                        if self.frames_manager.update_frame(frame_name, frame_data):
                            QMessageBox.information(
                                self.parent,
                                "Success",
                                f"Screenshot attached to frame '{frame_name}' successfully!",
                            )
                            self.logger.info(
                                f"Screenshot attached to frame: {frame_name}"
                            )
                            return True
                        else:
                            QMessageBox.warning(
                                self.parent,
                                "Error",
                                "Failed to update frame in database",
                            )
                            return False
                    else:
                        QMessageBox.information(
                            self.parent,
                            "Info",
                            "Screenshot already attached to this frame.",
                        )
                        return True

            QMessageBox.warning(self.parent, "Error", f"Frame '{frame_name}' not found")
            return False

        except Exception as e:
            self.logger.error(f"Error attaching screenshot to frame: {e}")
            QMessageBox.warning(
                self.parent, "Error", f"Failed to attach screenshot: {str(e)}"
            )
            return False

    def _save_frame_changes(
        self, original_name: str, updated_data: Dict, screenshots_to_delete: List[str]
    ):
        """Save changes to existing frame."""
        try:
            # Delete marked screenshots first
            for uuid_to_delete in screenshots_to_delete:
                try:
                    self.frames_manager.delete_screenshot(uuid_to_delete)
                    self.logger.info(f"Deleted screenshot: {uuid_to_delete}")
                except Exception as e:
                    self.logger.warning(
                        f"Could not delete screenshot {uuid_to_delete}: {e}"
                    )

            # Update frame data (name might have changed)
            if self.frames_manager.update_frame(original_name, updated_data):
                # If name changed, we need to update the key
                if original_name != updated_data.get("name"):
                    # This is handled by the update_frame method in FramesManager
                    pass

                QMessageBox.information(
                    self.parent,
                    "Success",
                    f"Frame '{updated_data.get('name')}' updated successfully!",
                )
                self.logger.info(
                    f"Frame updated: {original_name} -> {updated_data.get('name')}"
                )
                return True
            else:
                QMessageBox.warning(
                    self.parent, "Error", "Failed to update frame in database"
                )
                return False

        except Exception as e:
            self.logger.error(f"Error saving frame changes: {e}")
            QMessageBox.warning(
                self.parent, "Error", f"Failed to save changes: {str(e)}"
            )
            return False
