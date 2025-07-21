"""
Screenshot Manager Dialog Widget
"""

import logging
from pathlib import Path
from typing import Set
from PIL import Image
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont, QPixmap
from PyQt6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QWidget,
    QFrame,
    QGridLayout,
    QMessageBox,
)


class ScreenshotManagerDialog(QDialog):
    """Dialog for managing screenshots in frames."""

    def __init__(self, frame_data, frames_manager, parent_widget, parent=None):
        super().__init__(parent)
        self.frame_data = frame_data
        self.frames_manager = frames_manager
        self.parent_widget = parent_widget  # Store reference to parent widget for screenshot capture
        self.logger = logging.getLogger(__name__)

        # State management
        self.current_screenshots = frame_data.get("screenshots", []).copy()
        self.primary_screenshot = None
        self.marked_for_deletion: Set[str] = set()

        # Find primary screenshot
        for uuid in self.current_screenshots:
            screenshot_data = self.frames_manager.get_screenshot_data(uuid)
            if screenshot_data and screenshot_data.get("is_primary", False):
                self.primary_screenshot = uuid
                break

        # If no primary found, use first screenshot as primary
        if not self.primary_screenshot and self.current_screenshots:
            self.primary_screenshot = self.current_screenshots[0]

        self.setWindowTitle(f"Screenshot Manager - {frame_data.get('name', 'Unnamed')}")
        self.setModal(True)
        self.resize(900, 700)

        # Track selected screenshots (initialize early)
        self.selected_screenshots: Set[str] = set()

        self._setup_ui()

    def _setup_ui(self):
        """Setup screenshot manager UI."""
        layout = QVBoxLayout(self)

        # Title and buttons row
        title_and_buttons_layout = QHBoxLayout()

        # Title (left)
        title_label = QLabel(f"Managing Screenshots for: {self.frame_data.get('name', 'Unnamed Frame')}")
        title_label.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
        title_and_buttons_layout.addWidget(title_label)
        title_and_buttons_layout.addStretch()  # Push buttons to the right

        # Action buttons (right)
        self.make_primary_button = QPushButton("Make Primary")
        self.make_primary_button.clicked.connect(self._make_primary)
        self.make_primary_button.setEnabled(False)

        self.delete_button = QPushButton("Delete Selected")
        self.delete_button.clicked.connect(self._delete_selected)
        self.delete_button.setEnabled(False)

        self.new_screenshot_button = QPushButton("Add New Screenshot")
        self.new_screenshot_button.clicked.connect(self._add_new_screenshot)

        title_and_buttons_layout.addWidget(self.make_primary_button)
        title_and_buttons_layout.addWidget(self.delete_button)
        title_and_buttons_layout.addWidget(self.new_screenshot_button)

        layout.addLayout(title_and_buttons_layout)

        # Screenshots grid
        self.screenshots_scroll = QScrollArea()
        self.screenshots_scroll.setWidgetResizable(True)
        self.screenshots_scroll.setMinimumHeight(400)
        self.screenshots_scroll.setStyleSheet("QScrollArea { border: 2px solid #888; border-radius: 4px; }")

        self.screenshots_widget = QWidget()
        self.screenshots_layout = QGridLayout(self.screenshots_widget)
        self.screenshots_layout.setSpacing(10)

        self._refresh_screenshots_display()

        self.screenshots_scroll.setWidget(self.screenshots_widget)
        layout.addWidget(self.screenshots_scroll)

        # Dialog buttons (bottom)
        dialog_button_layout = QHBoxLayout()
        dialog_button_layout.addStretch()

        cancel_button = QPushButton("Cancel")
        cancel_button.clicked.connect(self._cancel_changes)

        save_button = QPushButton("Save Changes")
        save_button.clicked.connect(self._save_changes)

        dialog_button_layout.addWidget(cancel_button)
        dialog_button_layout.addWidget(save_button)
        layout.addLayout(dialog_button_layout)

        # set cancel as default button
        cancel_button.setDefault(True)

    def _refresh_screenshots_display(self):
        """Refresh the screenshots grid display."""
        # Clear existing widgets
        for i in reversed(range(self.screenshots_layout.count())):
            item = self.screenshots_layout.itemAt(i)
            if item and item.widget():
                widget = item.widget()
                if widget:
                    widget.setParent(None)

        # Display screenshots in 4-column grid
        row, col = 0, 0
        max_cols = 4

        for screenshot_uuid in self.current_screenshots:
            screenshot_widget = self._create_screenshot_widget(screenshot_uuid)
            self.screenshots_layout.addWidget(screenshot_widget, row, col)

            col += 1
            if col >= max_cols:
                col = 0
                row += 1

        if not self.current_screenshots:
            no_screenshots_label = QLabel("No screenshots available")
            no_screenshots_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.screenshots_layout.addWidget(no_screenshots_label, 0, 0)

    def _create_screenshot_widget(self, screenshot_uuid: str) -> QWidget:
        """Create widget for individual screenshot."""
        widget = QWidget()
        widget.setMaximumSize(200, 180)
        widget.setProperty("screenshot_uuid", screenshot_uuid)

        # Apply border styling based on state
        self._update_widget_styling(widget, screenshot_uuid)

        layout = QVBoxLayout(widget)
        layout.setContentsMargins(5, 5, 5, 5)

        # Find screenshot file
        screenshot_path = None
        screenshots_dir = self.frames_manager.screenshots_dir
        for file_path in screenshots_dir.glob(f"*{screenshot_uuid}*"):
            screenshot_path = file_path
            break

        # Screenshot thumbnail
        if screenshot_path and screenshot_path.exists():
            pixmap = QPixmap(str(screenshot_path))
            thumbnail = pixmap.scaled(
                150, 120, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation
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

        # Status label
        status_text = ""
        if screenshot_uuid == self.primary_screenshot:
            status_text += "PRIMARY "
        if screenshot_uuid in self.marked_for_deletion:
            status_text += "MARKED FOR DELETION"

        if status_text:
            status_label = QLabel(status_text)
            status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            status_label.setStyleSheet("font-weight: bold; color: blue;")
            layout.addWidget(status_label)

        # Make clickable for selection
        widget.mousePressEvent = lambda a0, uuid=screenshot_uuid: self._on_screenshot_clicked(uuid)

        return widget

    def _update_widget_styling(self, widget: QWidget, screenshot_uuid: str):
        """Update widget styling based on screenshot state."""
        styles = []

        # Primary screenshot gets green border
        if screenshot_uuid == self.primary_screenshot:
            styles.append("border: 3px solid green;")

        # Selected screenshots get blue border
        elif screenshot_uuid in self.selected_screenshots:
            styles.append("border: 3px solid blue;")

        # Marked for deletion gets red background
        if screenshot_uuid in self.marked_for_deletion:
            styles.append("background-color: rgba(255, 0, 0, 50);")

        # Default border
        if not styles or (
            screenshot_uuid not in self.selected_screenshots and screenshot_uuid != self.primary_screenshot
        ):
            styles.append("border: 1px solid gray;")

        widget.setStyleSheet(" ".join(styles))

    def _on_screenshot_clicked(self, screenshot_uuid: str):
        """Handle screenshot click for selection."""
        if screenshot_uuid in self.selected_screenshots:
            self.selected_screenshots.remove(screenshot_uuid)
        else:
            self.selected_screenshots.add(screenshot_uuid)

        # Update UI
        self._refresh_screenshots_display()
        self._update_button_states()

    def _update_button_states(self):
        """Update button enabled states based on selection."""
        has_selection = bool(self.selected_screenshots)
        single_selection = len(self.selected_screenshots) == 1

        self.make_primary_button.setEnabled(single_selection)
        self.delete_button.setEnabled(has_selection)

    def _make_primary(self):
        """Make selected screenshot primary."""
        if len(self.selected_screenshots) != 1:
            return

        new_primary = list(self.selected_screenshots)[0]
        if new_primary != self.primary_screenshot:
            self.primary_screenshot = new_primary
            self.selected_screenshots.clear()
            self._refresh_screenshots_display()
            self._update_button_states()

            # Enable regions button if we now have a primary
        # Removed regions_button reference

    def _delete_selected(self):
        """Mark/unmark selected screenshots for deletion."""
        for screenshot_uuid in self.selected_screenshots.copy():
            if screenshot_uuid in self.marked_for_deletion:
                # Unmark for deletion
                self.marked_for_deletion.remove(screenshot_uuid)
            else:
                # Mark for deletion (but can't delete primary)
                if screenshot_uuid != self.primary_screenshot:
                    self.marked_for_deletion.add(screenshot_uuid)
                else:
                    QMessageBox.warning(self, "Cannot Delete", "Cannot delete the primary screenshot.")

        self.selected_screenshots.clear()
        self._refresh_screenshots_display()
        self._update_button_states()

        # Removed _view_regions method

    def _add_new_screenshot(self):
        """Add new screenshot to frame."""
        try:
            # Get parent widget's screenshot capture method
            if hasattr(self.parent_widget, "_capture_playable_screenshot"):
                screenshot = self.parent_widget._capture_playable_screenshot()
                if screenshot:
                    # Convert QPixmap to PIL Image for saving
                    screenshot_path = Path.cwd() / "temp_new_screenshot.png"
                    screenshot.save(str(screenshot_path))
                    pil_image = Image.open(screenshot_path)

                    # Save screenshot and get UUID
                    screenshot_uuid = self.frames_manager.save_screenshot(pil_image, self.frame_data["name"])

                    # Add to current screenshots list
                    self.current_screenshots.append(screenshot_uuid)

                    # Refresh display
                    self._refresh_screenshots_display()

                    # Clean up temp file
                    screenshot_path.unlink()

                    QMessageBox.information(self, "Success", "Screenshot added successfully!")
                else:
                    QMessageBox.warning(self, "Error", "Failed to capture screenshot")
            else:
                QMessageBox.information(
                    self, "Feature Not Available", "Screenshot capture not available in this context."
                )

        except Exception as e:
            self.logger.error(f"Error adding new screenshot: {e}")
            QMessageBox.warning(self, "Error", f"Failed to add screenshot: {str(e)}")

    def _show_screenshot_popup(self, screenshot_uuid: str):
        """Show popup with larger screenshot view."""
        # Find screenshot file
        screenshot_path = None
        screenshots_dir = self.frames_manager.screenshots_dir
        for file_path in screenshots_dir.glob(f"*{screenshot_uuid}*"):
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
            650, 450, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation
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
            final_screenshots = [uuid for uuid in self.current_screenshots if uuid not in self.marked_for_deletion]

            # Update frame data
            self.frame_data["screenshots"] = final_screenshots

            # Actually delete the marked screenshots
            for uuid_to_delete in self.marked_for_deletion:
                try:
                    self.frames_manager.delete_screenshot(uuid_to_delete)
                except Exception as e:
                    print(f"Warning: Could not delete screenshot {uuid_to_delete}: {e}")

            # Save frame changes
            if self.frames_manager.update_frame(self.frame_data.get("name"), self.frame_data):
                QMessageBox.information(self, "Success", "Screenshots updated successfully!")
                self.accept()
            else:
                QMessageBox.warning(self, "Error", "Failed to save changes to database")

        except Exception as e:
            QMessageBox.warning(self, "Error", f"Failed to save changes: {str(e)}")
