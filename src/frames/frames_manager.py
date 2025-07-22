"""
Frames Manager - Combined UI and Coordination

Main frames management dialog combining UI and coordination functionality.
Handles frame management, dialog display, screenshot capture, and database operations.

Following project standards: KISS, no duplicated calculations, modular design.
"""

import logging
from pathlib import Path
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

from .utility.frames_management import FramesManagement
from .screenshot_manager import ScreenshotManagerDialog
from .widgets.edit_frame_dialog import EditFrameDialog

logger = logging.getLogger(__name__)


class FramesManager(QDialog):
    """Combined frames management dialog with all functionality"""

    def __init__(self, main_widget):
        super().__init__(main_widget)
        self.main_widget = main_widget

        # Initialize data management
        base_path = Path(__file__).parents[2]  # Go up from src/frames/frames_manager.py to project root
        self.frames_management = FramesManagement(base_path)

        # Get frames data and initialize dialog
        self.frames_list = self.frames_management.get_frame_list()
        self.selected_frame = None
        self.modified_frame_data = None
        self.screenshots_to_delete = []

        self.setWindowTitle("Frames Managemer")
        self.setModal(True)
        self._setup_ui()

        logger.info("FramesManager initialized")

    def _setup_ui(self):
        """Setup comprehensive frames management UI."""
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(2, 2, 2, 2)  # Reduce side/top/bottom margins (try 0, 4, or 8 for your taste)

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

        close_button = QPushButton("Close")
        close_button.clicked.connect(self.accept)

        button_layout.addWidget(close_button)

        right_panel.addLayout(button_layout)

        # Add panels to main layout
        main_layout.addWidget(left_widget, 1)
        main_layout.addWidget(right_widget, 2)

        # Set close as default button
        close_button.setDefault(True)
        # Initialize display
        if self.frames_list:
            self.dropdown.setCurrentIndex(0)
            self._on_frame_selected()

    def _create_frame_info_widget(self) -> QWidget:
        """Create widget for displaying frame information."""
        widget = QFrame()
        widget.setFrameStyle(QFrame.Shape.Box)
        layout = QFormLayout(widget)
        layout.setHorizontalSpacing(24)  # Increase spacing between label and field columns

        self.id_label = QLabel("--")
        self.name_label = QLabel("--")
        self.item_label = QLabel("--")
        self.automation_label = QLabel("--")
        self.screenshots_count_label = QLabel("--")
        self.text_regions_label = QLabel("--")
        self.interact_regions_label = QLabel("--")

        layout.addRow("ID:", self.id_label)
        layout.addRow("Name:", self.name_label)
        layout.addRow("Item:", self.item_label)

        # Declare horizontal line
        line1 = QFrame()
        line1.setFrameShape(QFrame.Shape.HLine)
        line1.setFrameShadow(QFrame.Shadow.Sunken)
        line1.setLineWidth(1)
        layout.addRow(line1)

        layout.addRow("Automation:", self.automation_label)
        layout.addRow("Screenshots:", self.screenshots_count_label)

        # Declare horizontal line
        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        line.setFrameShadow(QFrame.Shadow.Sunken)
        line.setLineWidth(1)
        layout.addRow(line)

        # Regions section (indented)
        regions_header = QLabel("Regions:")
        layout.addRow(regions_header)
        layout.addRow("    Text:", self.text_regions_label)
        layout.addRow("    Interact:", self.interact_regions_label)

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
            QMessageBox.warning(self, "Error", "Frames Database Failed to load")
            return

        # Update frame info
        self.id_label.setText(self.selected_frame.get("id", "Unknown"))
        self.name_label.setText(self.selected_frame.get("name", "Unnamed"))
        self.item_label.setText(self.selected_frame.get("item", "Unknown"))

        automation = "Yes" if self.selected_frame.get("automation", 0) == 1 else "No"
        self.automation_label.setText(automation)

        # Screenshots count
        screenshots = self.selected_frame.get("screenshots", [])
        self.screenshots_count_label.setText(str(len(screenshots)))

        # Regions
        regions = self.selected_frame.get("regions", {})
        text_regions = regions.get("text", [])
        text_region_count = len([r for r in text_regions if r.get("text", "").strip()])
        self.text_regions_label.setText(str(text_region_count))

        interact_regions = regions.get("interact", [])
        interact_region_count = len(interact_regions)
        self.interact_regions_label.setText(str(interact_region_count))

    def _manage_screenshots(self):
        """Open screenshot manager for selected frame."""
        if not self.selected_frame:
            QMessageBox.warning(self, "Error", "Please select a frame first")
            return

        dialog = ScreenshotManagerDialog(self.selected_frame, self.frames_management, self.main_widget, self)

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
        dialog = EditFrameDialog(self.selected_frame, self.frames_management.screenshots_dir, self)

        if dialog.exec() == QDialog.DialogCode.Accepted:
            modified_data, screenshots_to_delete = dialog.get_modified_data()
            if modified_data:
                original_name = self.selected_frame.get("name")
                if self._save_frame_changes(original_name, modified_data, screenshots_to_delete):
                    self._refresh_frames_list()

    def _drawer_test(self):
        """Drawer Test."""
        if not self.selected_frame:
            QMessageBox.warning(self, "Error", "Please select a frame first")
            return

    def _save_frame_changes(self, original_name: str, updated_data: Dict, screenshots_to_delete: List[str]) -> bool:
        """Save changes to existing frame."""
        try:
            # Delete marked screenshots first
            for uuid_to_delete in screenshots_to_delete:
                try:
                    self.frames_management.delete_screenshot(uuid_to_delete)
                except Exception as e:
                    print(f"Could not delete screenshot {uuid_to_delete}: {e}")

            # Update frame data
            if self.frames_management.update_frame(original_name, updated_data):
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
        self.frames_list = self.frames_management.get_frame_list()

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

    # Compatibility methods for the main overlay
    def show_frames_dialog(self):
        """Show the frames dialog - compatibility method."""
        try:
            self.show()
            self.activateWindow()
            self.raise_()
            logger.info("Frames dialog shown")
        except Exception as e:
            logger.error(f"Error showing frames dialog: {e}")

    def capture_playable_screenshot(self):
        """Capture a screenshot of the playable area"""
        try:
            # For now, this is a placeholder - in full implementation would capture screen
            # and use frames_management.save_screenshot()
            logger.info("Screenshot capture requested (placeholder)")
            return None
        except Exception as e:
            logger.error(f"Error capturing screenshot: {e}")
            return None

    def get_frames_data(self):
        """Get current frames data via utility"""
        return self.frames_management.get_frame_list()

    def get_selected_frame(self) -> Optional[Dict]:
        """Get currently selected frame."""
        return self.selected_frame

    def cleanup(self):
        """Cleanup resources"""
        try:
            self.close()
            logger.info("FramesManager cleaned up")
        except Exception as e:
            logger.error(f"Error during cleanup: {e}")
        """Cleanup resources"""
        try:
            if self.frames_dialog:
                self.frames_dialog.close()
                self.frames_dialog = None
            logger.info("FramesManager cleaned up")
        except Exception as e:
            logger.error(f"Error during cleanup: {e}")
