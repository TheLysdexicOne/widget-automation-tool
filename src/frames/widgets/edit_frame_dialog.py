"""
Edit Frame Dialog Widget - Single Frame Editor
"""

from pathlib import Path
from typing import Dict, Optional, Tuple, List
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont, QPixmap
from PyQt6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QFormLayout,
    QLabel,
    QPushButton,
    QLineEdit,
    QCheckBox,
    QScrollArea,
    QWidget,
    QFrame,
    QGridLayout,
    QMessageBox,
)


class ScreenshotGalleryWidget(QWidget):
    """Widget for displaying screenshot gallery with delete functionality."""

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
            screenshot_label.mousePressEvent = lambda ev, uuid=screenshot_uuid: self._on_screenshot_clicked(uuid)
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
        delete_button.clicked.connect(lambda: self._on_delete_clicked(screenshot_uuid, widget))

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
            coord_label.setText(f"({region['x']}, {region['y']}) {region['width']}x{region['height']}")
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
        self.screenshots_widget = ScreenshotGalleryWidget(screenshots, self.screenshots_dir, self)
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
            self.screenshots_to_delete = self.screenshots_widget.get_screenshots_to_delete()
            # Remove deleted screenshots from frame data
            for uuid_to_delete in self.screenshots_to_delete:
                if uuid_to_delete in self.modified_frame_data["screenshots"]:
                    self.modified_frame_data["screenshots"].remove(uuid_to_delete)

        self.accept()

    def get_modified_data(self) -> Tuple[Optional[Dict], List[str]]:
        """Get modified frame data and deletion list."""
        return self.modified_frame_data, self.screenshots_to_delete
