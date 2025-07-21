"""
Frames Dialog - Main Management Interface

Comprehensive frames management dialog with all functionality:
- Frame selection and display
- Frame details display with screenshot count
- Frame editing operations

Following project standards: KISS, no duplicated calculations, modular design.
"""

from typing import Dict, List, Optional

from PyQt6.QtWidgets import (
    QDialog,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QFormLayout,
    QLabel,
    QComboBox,
    QPushButton,
    QFrame,
    QMessageBox,
)
from PyQt6.QtGui import QFont

from ..screenshot_manager import ScreenshotManagerDialog
from .edit_frame_dialog import EditFrameDialog


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
        # self.resize(800, 400)
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
        self.interact_regions_label = QLabel("--")
        self.screenshots_count_label = QLabel("--")

        layout.addRow("ID:", self.id_label)
        layout.addRow("Name:", self.name_label)
        layout.addRow("Item:", self.item_label)
        layout.addRow("Automation:", self.automation_label)
        layout.addRow("Text Regions:", self.text_regions_label)
        layout.addRow("Interact Regions:", self.interact_regions_label)
        layout.addRow("Screenshots:", self.screenshots_count_label)

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
        text_region_count = len([r for r in text_regions if r.get("text", "").strip()])
        self.text_regions_label.setText(f"{text_region_count} regions defined")

        interact_regions = self.selected_frame.get("interact", [])
        interact_region_count = len([r for r in interact_regions if r.get("interact", "").strip()])
        self.interact_regions_label.setText(f"{interact_region_count} regions defined")

        # Update screenshots count
        screenshots = self.selected_frame.get("screenshots", [])
        self.screenshots_count_label.setText(f"{len(screenshots)} screenshots available")

    def _manage_screenshots(self):
        """Open screenshot manager for selected frame."""
        if not self.selected_frame:
            QMessageBox.warning(self, "Error", "Please select a frame first")
            return

        dialog = ScreenshotManagerDialog(self.selected_frame, self.frames_manager, self.parent_widget, self)

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
        dialog = EditFrameDialog(self.selected_frame, self.frames_manager.screenshots_dir, self)

        if dialog.exec() == QDialog.DialogCode.Accepted:
            modified_data, screenshots_to_delete = dialog.get_modified_data()
            if modified_data:
                original_name = self.selected_frame.get("name")
                if self._save_frame_changes(original_name, modified_data, screenshots_to_delete):
                    self._refresh_frames_list()

    def _save_frame_changes(self, original_name: str, updated_data: Dict, screenshots_to_delete: List[str]) -> bool:
        """Save changes to existing frame."""
        try:
            # Delete marked screenshots first
            for uuid_to_delete in screenshots_to_delete:
                try:
                    self.frames_manager.delete_screenshot(uuid_to_delete)
                except Exception as e:
                    print(f"Could not delete screenshot {uuid_to_delete}: {e}")

            # Update frame data
            if self.frames_manager.update_frame(original_name, updated_data):
                QMessageBox.information(
                    self,
                    "Success",
                    f"Frame '{updated_data.get('name')}' updated successfully!",
                )
                return True
            else:
                QMessageBox.warning(self, "Error", "Failed to update frame in database")
                return False

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
