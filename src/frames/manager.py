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
import shutil
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
    QComboBox,
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
        self.frames_db_path = base_path / "src" / "config" / "frames_database.json"
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


class FramesDialog(QDialog):
    """Comprehensive frames management dialog with all functionality."""

    def __init__(self, frames_list: List[Dict], frames_manager, parent=None):
        super().__init__(parent)
        self.frames_list = frames_list
        self.frames_manager = frames_manager
        self.parent_widget = parent
        self.selected_frame = None
        self.modified_frame_data = None
        self.screenshots_to_delete = []

        self.setWindowTitle("Frames Management")
        self.setModal(True)
        self.resize(1200, 800)
        self._setup_ui()

    def _setup_ui(self):
        """Setup comprehensive frames management UI."""
        main_layout = QHBoxLayout(self)

        # Left panel - Frame list and actions
        left_widget = QWidget()
        left_widget.setMaximumWidth(300)
        left_panel = QVBoxLayout(left_widget)

        # Frame selection dropdown
        selection_layout = QVBoxLayout()
        selection_layout.addWidget(QLabel("Select Frame:"))

        # Sort frames by tier numerically
        def tier_key(frame):
            tid = frame.get("id", "")
            try:
                return tuple(int(part) for part in tid.split("."))
            except Exception:
                return (9999,)  # fallback for missing/invalid id

        sorted_frames = sorted(self.frames_list, key=tier_key)
        self.dropdown = QComboBox()
        for frame in sorted_frames:
            tier = frame.get("id", "??")
            name = frame.get("name", "Unnamed")
            item = frame.get("item", "Unknown")
            self.dropdown.addItem(f"{tier}: {name} - ({item})", frame)

        self.dropdown.currentTextChanged.connect(self._on_frame_selected)
        selection_layout.addWidget(self.dropdown)
        left_panel.addLayout(selection_layout)

        # Action buttons
        actions_layout = QVBoxLayout()
        actions_layout.addWidget(QLabel("Actions:"))

        self.screenshots_btn = QPushButton("Screenshots")
        self.screenshots_btn.clicked.connect(self._manage_screenshots)
        self.screenshots_btn.setEnabled(False)
        actions_layout.addWidget(self.screenshots_btn)

        self.edit_frame_btn = QPushButton("Edit Selected Frame")
        self.edit_frame_btn.clicked.connect(self._edit_selected_frame)
        self.edit_frame_btn.setEnabled(False)
        actions_layout.addWidget(self.edit_frame_btn)

        left_panel.addLayout(actions_layout)
        left_panel.addStretch()

        # Right panel - Frame details and editing
        right_widget = QWidget()
        right_panel = QVBoxLayout(right_widget)

        # Frame details header
        details_header = QLabel("Frame Details")
        details_header.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
        right_panel.addWidget(details_header)

        # Frame info display
        self.frame_info_widget = self._create_frame_info_widget()
        right_panel.addWidget(self.frame_info_widget)

        # Screenshots section
        screenshots_header = QLabel("Screenshots")
        screenshots_header.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
        right_panel.addWidget(screenshots_header)

        self.screenshots_scroll = QScrollArea()
        self.screenshots_scroll.setWidgetResizable(True)
        self.screenshots_scroll.setMaximumHeight(300)
        right_panel.addWidget(self.screenshots_scroll)

        right_panel.addStretch()

        # Dialog buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()

        cancel_button = QPushButton("Close")
        cancel_button.clicked.connect(self.accept)
        button_layout.addWidget(cancel_button)

        right_panel.addLayout(button_layout)

        # Add panels to main layout
        main_layout.addWidget(left_widget, 1)
        main_layout.addWidget(right_widget, 2)

        # Initialize display
        if self.frames_list:
            self.dropdown.setCurrentIndex(0)
            self._on_frame_selected()

    def _create_frame_info_widget(self) -> QWidget:
        """Create widget for displaying frame information."""
        widget = QFrame()
        widget.setFrameStyle(QFrame.Shape.Box)
        layout = QFormLayout(widget)

        self.id_label = QLabel("--")
        self.name_label = QLabel("--")
        self.item_label = QLabel("--")
        self.automation_label = QLabel("--")
        self.text_regions_label = QLabel("--")

        layout.addRow("ID:", self.id_label)
        layout.addRow("Name:", self.name_label)
        layout.addRow("Item:", self.item_label)
        layout.addRow("Automation:", self.automation_label)
        layout.addRow("Text Regions:", self.text_regions_label)

        return widget

    def _on_frame_selected(self):
        """Handle frame selection change."""
        current_data = self.dropdown.currentData()
        if current_data:
            self.selected_frame = current_data
            self._update_frame_display()
            self.edit_frame_btn.setEnabled(True)
            self.screenshots_btn.setEnabled(True)
        else:
            self.selected_frame = None
            self.edit_frame_btn.setEnabled(False)
            self.screenshots_btn.setEnabled(False)

    def _update_frame_display(self):
        """Update the display with selected frame data."""
        if not self.selected_frame:
            return

        # Update frame info
        self.id_label.setText(self.selected_frame.get("id", "Unknown"))
        self.name_label.setText(self.selected_frame.get("name", "Unnamed"))
        self.item_label.setText(self.selected_frame.get("item", "Unknown"))

        automation = "Yes" if self.selected_frame.get("automation", 0) == 1 else "No"
        self.automation_label.setText(automation)

        text_regions = self.selected_frame.get("text", [])
        region_count = len([r for r in text_regions if r.get("text", "").strip()])
        self.text_regions_label.setText(f"{region_count} regions defined")

        # Update screenshots gallery
        self._update_screenshots_display()

    def _update_screenshots_display(self):
        """Update screenshots gallery for selected frame."""
        if not self.selected_frame:
            return

        screenshots = self.selected_frame.get("screenshots", [])
        screenshots_widget = ScreenshotGalleryWidget(
            screenshots, self.frames_manager.screenshots_dir, self
        )
        screenshots_widget.screenshot_clicked.connect(self._show_screenshot_popup)

        self.screenshots_scroll.setWidget(screenshots_widget)

    def _show_screenshot_popup(self, screenshot_uuid: str):
        """Show popup with larger screenshot view."""
        # Find screenshot file
        screenshot_path = None
        for file_path in self.frames_manager.screenshots_dir.glob(
            f"*{screenshot_uuid}*"
        ):
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

    def _manage_screenshots(self):
        """Open screenshot manager for selected frame."""
        if not self.selected_frame:
            QMessageBox.warning(self, "Error", "Please select a frame first")
            return

        dialog = ScreenshotManagerDialog(
            self.selected_frame, self.frames_manager, self.parent_widget, self
        )

        if dialog.exec() == QDialog.DialogCode.Accepted:
            # Refresh the display to show updated screenshot count
            self._refresh_frames_list()
            self._update_frame_display()

    def _edit_selected_frame(self):
        """Edit the selected frame."""
        if not self.selected_frame:
            QMessageBox.warning(self, "Error", "Please select a frame first")
            return

        # Show edit dialog for single frame
        dialog = EditFrameDialog(
            self.selected_frame, self.frames_manager.screenshots_dir, self
        )

        if dialog.exec() == QDialog.DialogCode.Accepted:
            modified_data, screenshots_to_delete = dialog.get_modified_data()
            if modified_data:
                original_name = self.selected_frame.get("name")
                if self._save_frame_changes(
                    original_name, modified_data, screenshots_to_delete
                ):
                    self._refresh_frames_list()

    def _save_frame_changes(
        self, original_name: str, updated_data: Dict, screenshots_to_delete: List[str]
    ) -> bool:
        """Save changes to existing frame."""
        try:
            menu_system = FramesMenuSystem(self.parent_widget, self.frames_manager)
            menu_system._save_frame_changes(
                original_name, updated_data, screenshots_to_delete
            )
            return True
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Failed to save changes: {str(e)}")
            return False

    def _refresh_frames_list(self):
        """Refresh the frames list and update dropdown."""
        self.frames_list = self.frames_manager.get_frame_list()

        # Save current selection
        current_frame_name = None
        if self.selected_frame:
            current_frame_name = self.selected_frame.get("name")

        # Clear and repopulate dropdown
        self.dropdown.clear()

        # Sort frames by tier numerically
        def tier_key(frame):
            tid = frame.get("id", "")
            try:
                return tuple(int(part) for part in tid.split("."))
            except Exception:
                return (9999,)

        sorted_frames = sorted(self.frames_list, key=tier_key)

        # Repopulate
        for frame in sorted_frames:
            tier = frame.get("id", "??")
            name = frame.get("name", "Unnamed")
            item = frame.get("item", "Unknown")
            self.dropdown.addItem(f"{tier}: {name} - ({item})", frame)

        # Restore selection if possible
        if current_frame_name:
            for i in range(self.dropdown.count()):
                frame_data = self.dropdown.itemData(i)
                if frame_data and frame_data.get("name") == current_frame_name:
                    self.dropdown.setCurrentIndex(i)
                    break

        self._on_frame_selected()

    def get_selected_frame(self) -> Optional[Dict]:
        return self.selected_frame


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


class ScreenshotManagerDialog(QDialog):
    """Dialog for managing frame screenshots with primary selection and staging changes."""

    def __init__(self, frame_data: Dict, frames_manager, parent_widget, parent=None):
        super().__init__(parent)
        self.frame_data = frame_data
        self.frames_manager = frames_manager
        self.parent_widget = parent_widget  # For screenshot capture
        self.original_screenshots = frame_data.get("screenshots", []).copy()
        self.current_screenshots = frame_data.get("screenshots", []).copy()
        self.marked_for_deletion = set()
        self.selected_screenshots = set()
        self.screenshot_widgets = {}

        self.setWindowTitle("Screenshot Manager")
        self.setModal(True)
        self.resize(800, 600)
        self._setup_ui()

    def _setup_ui(self):
        """Setup screenshot manager UI."""
        layout = QVBoxLayout(self)

        # Title
        title_label = QLabel(
            f"Screenshots for: {self.frame_data.get('name', 'Unnamed Frame')}"
        )
        title_label.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
        layout.addWidget(title_label)

        # Action buttons at top
        action_layout = QHBoxLayout()

        # Left side buttons
        left_buttons = QHBoxLayout()
        self.make_primary_btn = QPushButton("Make Primary")
        self.make_primary_btn.clicked.connect(self._make_primary)
        self.make_primary_btn.setEnabled(False)

        self.delete_btn = QPushButton("Delete")
        self.delete_btn.clicked.connect(self._mark_for_deletion)
        self.delete_btn.setEnabled(False)

        left_buttons.addWidget(self.make_primary_btn)
        left_buttons.addWidget(self.delete_btn)
        left_buttons.addStretch()

        # Right side buttons
        right_buttons = QHBoxLayout()
        self.regions_btn = QPushButton("Regions")
        self.regions_btn.clicked.connect(self._view_regions)
        self.regions_btn.setEnabled(len(self.current_screenshots) > 0)

        self.new_btn = QPushButton("New")
        self.new_btn.clicked.connect(self._take_new_screenshot)

        right_buttons.addStretch()
        right_buttons.addWidget(self.regions_btn)
        right_buttons.addWidget(self.new_btn)

        action_layout.addLayout(left_buttons)
        action_layout.addLayout(right_buttons)
        layout.addLayout(action_layout)

        # Screenshots gallery
        self.screenshots_scroll = QScrollArea()
        self.screenshots_scroll.setWidgetResizable(True)
        self._update_screenshots_display()
        layout.addWidget(self.screenshots_scroll)

        # Bottom buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()

        cancel_button = QPushButton("Cancel")
        cancel_button.clicked.connect(self._cancel_changes)

        save_button = QPushButton("Save")
        save_button.clicked.connect(self._save_changes)

        button_layout.addWidget(cancel_button)
        button_layout.addWidget(save_button)
        layout.addLayout(button_layout)

    def _update_screenshots_display(self):
        """Update the screenshots gallery display."""
        widget = QWidget()
        layout = QGridLayout(widget)

        self.screenshot_widgets = {}
        row, col = 0, 0
        max_cols = 4

        for i, screenshot_uuid in enumerate(self.current_screenshots):
            screenshot_widget = self._create_screenshot_widget(
                screenshot_uuid, i == 0
            )  # First is primary
            layout.addWidget(screenshot_widget, row, col)
            self.screenshot_widgets[screenshot_uuid] = screenshot_widget

            col += 1
            if col >= max_cols:
                col = 0
                row += 1

        if not self.current_screenshots:
            no_screenshots_label = QLabel(
                "No screenshots available\nClick 'New' to add a screenshot"
            )
            no_screenshots_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            no_screenshots_label.setStyleSheet("color: gray; font-size: 14px;")
            layout.addWidget(no_screenshots_label, 0, 0, 1, max_cols)

        self.screenshots_scroll.setWidget(widget)

    def _create_screenshot_widget(
        self, screenshot_uuid: str, is_primary: bool
    ) -> QWidget:
        """Create widget for individual screenshot with checkbox."""
        container = QFrame()
        container.setFrameStyle(QFrame.Shape.Box)
        container.setMaximumSize(150, 120)
        container.setMinimumSize(150, 120)

        # Set border color - green for primary, normal for others
        if is_primary:
            container.setStyleSheet("QFrame { border: 3px solid green; }")
        elif screenshot_uuid in self.marked_for_deletion:
            container.setStyleSheet(
                "QFrame { border: 2px solid red; background-color: rgba(255, 0, 0, 30); }"
            )
        else:
            container.setStyleSheet("QFrame { border: 1px solid gray; }")

        # Use absolute positioning for precise control
        container_layout = QVBoxLayout(container)
        container_layout.setContentsMargins(5, 5, 5, 5)
        container_layout.setSpacing(0)

        # Find screenshot file
        screenshot_path = None
        for file_path in self.frames_manager.screenshots_dir.glob(
            f"*{screenshot_uuid}*"
        ):
            screenshot_path = file_path
            break

        # Create a widget to hold the image and checkbox
        content_widget = QWidget()
        content_widget.setFixedSize(140, 110)

        # Screenshot image
        if screenshot_path and screenshot_path.exists():
            pixmap = QPixmap(str(screenshot_path))
            thumbnail = pixmap.scaled(
                140,
                110,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation,
            )

            screenshot_label = QLabel(content_widget)
            screenshot_label.setPixmap(thumbnail)
            screenshot_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            screenshot_label.setGeometry(0, 0, 140, 110)
            screenshot_label.mousePressEvent = (
                lambda e, uuid=screenshot_uuid: self._on_screenshot_clicked(uuid, e)
            )
        else:
            # Missing file placeholder
            placeholder = QLabel("Missing\nFile", content_widget)
            placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
            placeholder.setStyleSheet("color: red;")
            placeholder.setGeometry(0, 0, 140, 110)

        # Checkbox in upper-left corner (overlay on image)
        checkbox = QCheckBox(content_widget)
        checkbox.setGeometry(5, 5, 20, 20)
        checkbox.setStyleSheet(
            """
            QCheckBox {
                background-color: rgba(255, 255, 255, 200);
                border: 1px solid gray;
                border-radius: 3px;
            }
            QCheckBox::indicator {
                width: 16px;
                height: 16px;
            }
        """
        )
        checkbox.stateChanged.connect(
            lambda state, uuid=screenshot_uuid: self._on_checkbox_changed(uuid, state)
        )

        # Set checkbox state based on selection
        checkbox.setChecked(screenshot_uuid in self.selected_screenshots)

        # Disable checkbox for primary if it's the only screenshot
        if is_primary and len(self.current_screenshots) == 1:
            checkbox.setEnabled(False)
            checkbox.setToolTip(
                "Cannot select primary screenshot when it's the only one"
            )

        container_layout.addWidget(content_widget)

        return container

    def _on_screenshot_clicked(self, screenshot_uuid: str, event):
        """Handle screenshot click for preview."""
        # Show larger preview
        self._show_screenshot_popup(screenshot_uuid)

    def _on_checkbox_changed(self, screenshot_uuid: str, state):
        """Handle checkbox state change."""
        if state == Qt.CheckState.Checked.value:
            self.selected_screenshots.add(screenshot_uuid)
        else:
            self.selected_screenshots.discard(screenshot_uuid)

        self._update_action_buttons()

    def _update_action_buttons(self):
        """Update action button states based on selection."""
        selected_count = len(self.selected_screenshots)

        if selected_count == 0:
            self.make_primary_btn.setEnabled(False)
            self.delete_btn.setEnabled(False)
        elif selected_count == 1:
            self.make_primary_btn.setEnabled(True)
            self.delete_btn.setEnabled(True)
        else:  # Multiple selected
            self.make_primary_btn.setEnabled(False)  # Can't make multiple primary
            self.delete_btn.setEnabled(True)

    def _make_primary(self):
        """Make selected screenshot primary."""
        if len(self.selected_screenshots) != 1:
            return

        selected_uuid = next(iter(self.selected_screenshots))

        # Move to front of list
        if selected_uuid in self.current_screenshots:
            self.current_screenshots.remove(selected_uuid)
            self.current_screenshots.insert(0, selected_uuid)

        # Clear selection and refresh
        self.selected_screenshots.clear()
        self._update_screenshots_display()
        self._update_action_buttons()

        # Update regions button state
        self.regions_btn.setEnabled(len(self.current_screenshots) > 0)

    def _mark_for_deletion(self):
        """Mark selected screenshots for deletion."""
        for screenshot_uuid in self.selected_screenshots:
            # Don't allow deletion of primary if it's the only screenshot
            if (
                screenshot_uuid == self.current_screenshots[0]
                and len(self.current_screenshots) == 1
            ):
                QMessageBox.warning(
                    self,
                    "Cannot Delete",
                    "Cannot delete the primary screenshot when it's the only one.",
                )
                continue

            self.marked_for_deletion.add(screenshot_uuid)

        # Clear selection and refresh
        self.selected_screenshots.clear()
        self._update_screenshots_display()
        self._update_action_buttons()

    def _take_new_screenshot(self):
        """Take a new screenshot and add to gallery."""
        try:
            # Bring WidgetInc.exe to focus if available
            if (
                WIN32_AVAILABLE
                and hasattr(self.parent_widget, "target_hwnd")
                and self.parent_widget.target_hwnd
            ):
                win32gui.SetForegroundWindow(self.parent_widget.target_hwnd)
                time.sleep(0.5)  # Give time for window to come to front

            # Capture screenshot using parent's method
            menu_system = FramesMenuSystem(self.parent_widget, self.frames_manager)
            screenshot = menu_system._capture_playable_screenshot()

            if screenshot:
                # Convert to PIL and save
                screenshot_path = Path.cwd() / "temp_new_screenshot.png"
                screenshot.save(str(screenshot_path))
                pil_image = Image.open(screenshot_path)

                # Save screenshot and get UUID
                screenshot_uuid = self.frames_manager.save_screenshot(
                    pil_image, self.frame_data.get("name", "unnamed")
                )

                # Add to current screenshots list
                self.current_screenshots.append(screenshot_uuid)

                # Clean up temp file
                screenshot_path.unlink()

                # Refresh display
                self._update_screenshots_display()

                # Update regions button state
                self.regions_btn.setEnabled(len(self.current_screenshots) > 0)

                # Bring this dialog back to front
                self.raise_()
                self.activateWindow()

                QMessageBox.information(
                    self, "Success", "New screenshot added successfully!"
                )

            else:
                QMessageBox.warning(self, "Error", "Failed to capture screenshot")

        except Exception as e:
            QMessageBox.warning(self, "Error", f"Failed to take screenshot: {str(e)}")

    def _view_regions(self):
        """View regions for the primary screenshot."""
        if not self.current_screenshots:
            return

        primary_uuid = self.current_screenshots[0]

        # Find screenshot file
        screenshot_path = None
        for file_path in self.frames_manager.screenshots_dir.glob(f"*{primary_uuid}*"):
            screenshot_path = file_path
            break

        if not screenshot_path or not screenshot_path.exists():
            QMessageBox.warning(self, "Error", "Primary screenshot file not found")
            return

        # Show regions viewer
        dialog = RegionsViewerDialog(screenshot_path, self.frame_data, self)
        dialog.exec()

    def _show_screenshot_popup(self, screenshot_uuid: str):
        """Show popup with larger screenshot view."""
        screenshot_path = None
        for file_path in self.frames_manager.screenshots_dir.glob(
            f"*{screenshot_uuid}*"
        ):
            screenshot_path = file_path
            break

        if not screenshot_path or not screenshot_path.exists():
            QMessageBox.warning(self, "Error", "Screenshot file not found")
            return

        # Create popup dialog
        popup = QDialog(self)
        popup.setWindowTitle("Screenshot Preview")
        popup.setModal(True)
        popup.resize(700, 500)

        layout = QVBoxLayout(popup)

        # Screenshot display
        screenshot_label = QLabel()
        pixmap = QPixmap(str(screenshot_path))
        scaled_pixmap = pixmap.scaled(
            650,
            450,
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

    def _cancel_changes(self):
        """Cancel all changes and close dialog."""
        self.reject()

    def _save_changes(self):
        """Save all changes to the frame."""
        try:
            # Remove screenshots marked for deletion from current list
            final_screenshots = [
                uuid
                for uuid in self.current_screenshots
                if uuid not in self.marked_for_deletion
            ]

            # Update frame data
            self.frame_data["screenshots"] = final_screenshots

            # Actually delete the marked screenshots
            for uuid_to_delete in self.marked_for_deletion:
                try:
                    self.frames_manager.delete_screenshot(uuid_to_delete)
                except Exception as e:
                    print(f"Warning: Could not delete screenshot {uuid_to_delete}: {e}")

            # Save frame changes
            if self.frames_manager.update_frame(
                self.frame_data.get("name"), self.frame_data
            ):
                QMessageBox.information(
                    self, "Success", "Screenshots updated successfully!"
                )
                self.accept()
            else:
                QMessageBox.warning(self, "Error", "Failed to save changes to database")

        except Exception as e:
            QMessageBox.warning(self, "Error", f"Failed to save changes: {str(e)}")


class RegionsViewerDialog(QDialog):
    """Dialog for viewing text regions overlaid on primary screenshot."""

    def __init__(self, screenshot_path: Path, frame_data: Dict, parent=None):
        super().__init__(parent)
        self.screenshot_path = screenshot_path
        self.frame_data = frame_data

        self.setWindowTitle("Regions Viewer")
        self.setModal(True)
        self.resize(900, 700)
        self._setup_ui()

    def _setup_ui(self):
        """Setup regions viewer UI."""
        layout = QVBoxLayout(self)

        # Title
        title_label = QLabel(
            f"Text Regions for: {self.frame_data.get('name', 'Unnamed Frame')}"
        )
        title_label.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
        layout.addWidget(title_label)

        # Create a widget to display the screenshot with regions
        self.regions_widget = RegionsDisplayWidget(
            self.screenshot_path, self.frame_data
        )
        scroll_area = QScrollArea()
        scroll_area.setWidget(self.regions_widget)
        scroll_area.setWidgetResizable(True)
        layout.addWidget(scroll_area)

        # Regions information
        info_layout = QVBoxLayout()
        info_label = QLabel("Text Regions:")
        info_label.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
        info_layout.addWidget(info_label)

        text_regions = self.frame_data.get("text", [])
        if text_regions:
            for i, region in enumerate(text_regions):
                region_info = region.get("region", {})
                text_info = region.get("text", "")
                info_text = f"Region {i+1}: \"{text_info}\" at ({region_info.get('x', 0)}, {region_info.get('y', 0)}) {region_info.get('width', 0)}x{region_info.get('height', 0)}"
                info_layout.addWidget(QLabel(info_text))
        else:
            info_layout.addWidget(QLabel("No text regions defined"))

        layout.addLayout(info_layout)

        # Close button
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        close_button = QPushButton("Close")
        close_button.clicked.connect(self.accept)
        button_layout.addWidget(close_button)
        layout.addLayout(button_layout)


class RegionsDisplayWidget(QWidget):
    """Widget to display screenshot with text regions overlaid."""

    def __init__(self, screenshot_path: Path, frame_data: Dict, parent=None):
        super().__init__(parent)
        self.screenshot_path = screenshot_path
        self.frame_data = frame_data
        self.scale_factor = 0.8  # Scale down for viewing

        # Load screenshot
        self.pixmap = QPixmap(str(screenshot_path))
        if not self.pixmap.isNull():
            # Scale the pixmap
            self.scaled_pixmap = self.pixmap.scaled(
                int(self.pixmap.width() * self.scale_factor),
                int(self.pixmap.height() * self.scale_factor),
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation,
            )
            self.setFixedSize(self.scaled_pixmap.size())
        else:
            self.scaled_pixmap = QPixmap()
            self.setFixedSize(400, 300)

    def paintEvent(self, event):
        """Paint the screenshot with regions overlaid."""
        painter = QPainter(self)

        # Draw screenshot
        if not self.scaled_pixmap.isNull():
            painter.drawPixmap(0, 0, self.scaled_pixmap)

        # Draw text regions
        text_regions = self.frame_data.get("text", [])
        colors = [
            QColor(0, 255, 255, 120),  # Cyan
            QColor(255, 165, 0, 120),  # Orange
            QColor(0, 255, 0, 120),  # Green
        ]

        for i, region in enumerate(text_regions):
            region_info = region.get("region", {})
            if not region_info:
                continue

            # Scale region coordinates
            x = int(region_info.get("x", 0) * self.scale_factor)
            y = int(region_info.get("y", 0) * self.scale_factor)
            width = int(region_info.get("width", 0) * self.scale_factor)
            height = int(region_info.get("height", 0) * self.scale_factor)

            # Draw region box
            color = colors[i % len(colors)]
            painter.setPen(QPen(color, 2))
            painter.setBrush(QBrush(color))
            painter.drawRect(x, y, width, height)

            # Draw region label
            text = region.get("text", f"Region {i+1}")
            painter.setPen(QPen(QColor(255, 255, 255), 2))
            painter.drawText(x + 5, y + 15, text)


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


class EditFrameDialog(QDialog):
    """Dialog for editing a single frame."""

    def __init__(self, frame_data: Dict, screenshots_dir: Path, parent=None):
        super().__init__(parent)
        self.frame_data = frame_data
        self.screenshots_dir = screenshots_dir
        self.modified_frame_data = None
        self.screenshots_to_delete = []

        self.setWindowTitle(f"Edit Frame: {frame_data.get('name', 'Unnamed')}")
        self.setModal(True)
        self.resize(700, 600)
        self._setup_ui()

    def _setup_ui(self):
        """Setup single frame edit UI."""
        layout = QVBoxLayout(self)

        # Form section
        form_layout = QFormLayout()

        # Item and Frame fields
        item_frame_layout = QHBoxLayout()
        self.item_edit = QLineEdit(self.frame_data.get("item", ""))
        self.frame_edit = QLineEdit(self.frame_data.get("name", ""))
        item_frame_layout.addWidget(QLabel("Item:"))
        item_frame_layout.addWidget(self.item_edit)
        item_frame_layout.addWidget(QLabel("Frame:"))
        item_frame_layout.addWidget(self.frame_edit)

        # Can be automated checkbox
        self.automation_checkbox = QCheckBox("Can be automated")
        self.automation_checkbox.setChecked(self.frame_data.get("automation", 0) == 1)

        form_layout.addRow(item_frame_layout)
        form_layout.addRow(self.automation_checkbox)

        # Text regions section
        regions_label = QLabel("Text Regions:")
        regions_label.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
        form_layout.addRow(regions_label)

        self.regions_layout = QVBoxLayout()
        self._setup_regions()
        form_layout.addRow(self.regions_layout)

        layout.addLayout(form_layout)

        # Screenshots section
        screenshots_header = QLabel("Screenshots")
        screenshots_header.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
        layout.addWidget(screenshots_header)

        self.screenshots_scroll = QScrollArea()
        self.screenshots_scroll.setWidgetResizable(True)
        self.screenshots_scroll.setMaximumHeight(200)
        self._setup_screenshots()
        layout.addWidget(self.screenshots_scroll)

        # Dialog buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()

        cancel_button = QPushButton("Cancel")
        cancel_button.clicked.connect(self.reject)

        save_button = QPushButton("Save")
        save_button.clicked.connect(self._save_changes)

        button_layout.addWidget(cancel_button)
        button_layout.addWidget(save_button)
        layout.addLayout(button_layout)

    def _setup_regions(self):
        """Setup text regions editing."""
        self.regions = []
        text_regions = self.frame_data.get("text", [])

        for i in range(3):  # Support up to 3 regions
            self._add_region_row(i, text_regions[i] if i < len(text_regions) else None)

    def _add_region_row(self, index: int, region_data: Optional[Dict]):
        """Add a text region row."""
        row_layout = QHBoxLayout()

        text_edit = QLineEdit()
        if region_data:
            text_edit.setText(region_data.get("text", ""))
        text_edit.setPlaceholderText("Enter text description")

        coord_label = QLabel("No region selected")
        if region_data and region_data.get("region"):
            region = region_data["region"]
            coord_label.setText(
                f"({region['x']}, {region['y']}) {region['width']}x{region['height']}"
            )
        coord_label.setMinimumWidth(150)

        row_layout.addWidget(QLabel("Text:"))
        row_layout.addWidget(text_edit)
        row_layout.addWidget(QLabel("Region:"))
        row_layout.addWidget(coord_label)

        # Store references
        region_info = {
            "text_edit": text_edit,
            "coord_label": coord_label,
            "region": region_data.get("region") if region_data else None,
        }
        self.regions.append(region_info)
        self.regions_layout.addLayout(row_layout)

    def _setup_screenshots(self):
        """Setup screenshots gallery."""
        screenshots = self.frame_data.get("screenshots", [])
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
        # Collect text regions
        text_regions = []
        for region_info in self.regions:
            text = region_info["text_edit"].text().strip()
            if text and region_info["region"]:
                text_regions.append({"text": text, "region": region_info["region"]})

        self.modified_frame_data = {
            "id": self.frame_data.get("id"),  # Keep original ID
            "name": self.frame_edit.text().strip(),
            "item": self.item_edit.text().strip(),
            "automation": 1 if self.automation_checkbox.isChecked() else 0,
            "text": text_regions,
            "screenshots": self.frame_data.get("screenshots", []),
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

    def get_modified_data(self) -> Tuple[Optional[Dict], List[str]]:
        """Get modified frame data and deletion list."""
        return self.modified_frame_data, self.screenshots_to_delete


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

        # Sort frames by tier numerically
        def tier_key(frame):
            tid = frame.get("id", "")
            try:
                return tuple(int(part) for part in tid.split("."))
            except Exception:
                return (9999,)  # fallback for missing/invalid id

        sorted_frames = sorted(self.frames_list, key=tier_key)

        self.frames_list_widget = QListWidget()
        self.frames_list_widget.itemClicked.connect(self._on_frame_selected)
        self.frames_list_widget.setMaximumWidth(200)

        # Populate frame list
        for frame in sorted_frames:
            tier = frame.get("id", "??")
            name = frame.get("name", "Unnamed")
            item = QListWidgetItem(f"{tier}: {name}")
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
        """Show the main FRAMES menu - now simplified to just open the comprehensive dialog."""
        # Directly show the comprehensive frames dialog
        frames_list = self.frames_manager.get_frame_list()
        if not frames_list:
            QMessageBox.information(
                self.parent,
                "No Frames",
                "No frames available. Create a frame first using 'Add New Frame'.",
            )
            return
        dialog = FramesDialog(frames_list, self.frames_manager, self.parent)
        dialog.exec()

    def _show_frames_dialog(self):
        """Show comprehensive frames management dialog."""
        frames_list = self.frames_manager.get_frame_list()
        if not frames_list:
            QMessageBox.information(
                self.parent,
                "No Frames",
                "No frames available. Create a frame first using 'Add New Frame'.",
            )
            return
        dialog = FramesDialog(frames_list, self.frames_manager, self.parent)
        dialog.exec()

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
