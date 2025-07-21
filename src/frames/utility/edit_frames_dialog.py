"""
Edit Frames Dialog Widget
"""

from pathlib import Path
from typing import Dict, Optional, Tuple, List
from PyQt6.QtCore import Qt
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
    QListWidget,
    QListWidgetItem,
    QScrollArea,
    QMessageBox,
)
from ..widgets.screenshot_gallery_widget import ScreenshotGalleryWidget


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
            self.screenshots_to_delete = self.screenshots_widget.get_screenshots_to_delete()
            # Remove deleted screenshots from frame data
            for uuid_to_delete in self.screenshots_to_delete:
                if uuid_to_delete in self.modified_frame_data["screenshots"]:
                    self.modified_frame_data["screenshots"].remove(uuid_to_delete)

        self.accept()

    def get_modified_data(self) -> Tuple[Optional[str], Optional[Dict], List[str]]:
        """Get modified frame data and deletion list."""
        original_name = self.selected_frame.get("name") if self.selected_frame else None
        return original_name, self.modified_frame_data, self.screenshots_to_delete
