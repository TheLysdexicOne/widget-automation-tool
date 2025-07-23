"""
Frames Manager - Combined UI and Coordination

Main frames management dialog combining UI and coordination functionality.
Handles frame management, dialog display, screenshot capture, and database operations.

Following project standards: KISS, no duplicated calculations, modular design.
"""

from PyQt6.QtCore import Qt
import logging
from pathlib import Path


from PyQt6.QtWidgets import (
    QDialog,
    QWidget,
    QFormLayout,
    QLabel,
    QFrame,
    QMessageBox,
    QVBoxLayout,
    QHBoxLayout,
    QComboBox,
    QPushButton,
)


from utility.database_manager import DatabaseManager

logger = logging.getLogger(__name__)


class FrameManager(QDialog):
    """Combined frames management dialog with all functionality"""

    def __init__(self, main_widget):
        super().__init__(main_widget)
        self.main_widget = main_widget

        # Initialize data management
        base_path = Path(__file__).parents[2]  # Go up from src/overlay/frame_manager.py to project root
        self.frames_management = DatabaseManager(base_path)

        # Get frames data and initialize dialog
        self.frames_list = self.frames_management.get_frame_list()
        self.selected_frame = None
        self.modified_frame_data = None
        self.screenshots_to_delete = []

        # Track last update check for global update system
        self.last_frames_check = 0.0

        self.setWindowTitle("Frames Manager")
        # self.setModal(True)  # Make modeless
        self.setWindowFlags(Qt.WindowType.Dialog)
        self._setup_ui()

        logger.info("FrameManager initialized")

    def _setup_ui(self):
        """Setup simplified single-column frames management UI."""
        # All required widgets are already imported at the top

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(8, 8, 8, 8)
        main_layout.setSpacing(10)

        # Frame selection (top)
        main_layout.addWidget(QLabel("Select Frame:"))

        def tier_key(frame):
            tid = frame.get("id", "")
            try:
                return tuple(int(part) for part in tid.split("."))
            except Exception:
                return (9999,)

        sorted_frames = sorted(self.frames_list, key=tier_key)
        self.dropdown = QComboBox()
        self.dropdown.setEnabled(True)
        self.dropdown.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        for frame in sorted_frames:
            self.dropdown.addItem(
                f"{frame.get('id', '??')}: {frame.get('name', 'Unnamed')} - ({frame.get('item', 'Unknown')})", frame
            )
        self.dropdown.currentIndexChanged.connect(self._on_frame_selected)
        main_layout.addWidget(self.dropdown)

        # Frame details (middle)
        self.frame_info_widget = self._create_frame_info_widget()
        main_layout.addWidget(self.frame_info_widget)

        # Buttons (bottom)
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        self.edit_frame_btn = QPushButton("Edit Frame")
        self.edit_frame_btn.setEnabled(False)
        self.edit_frame_btn.clicked.connect(self._edit_selected_frame)
        button_layout.addWidget(self.edit_frame_btn)
        close_button = QPushButton("Close")
        close_button.clicked.connect(self.accept)
        button_layout.addWidget(close_button)
        main_layout.addLayout(button_layout)

        main_layout.addStretch()

        # Initialize display: always select the first frame if available
        if self.dropdown.count() > 0:
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
            if hasattr(self, "edit_frame_btn"):
                self.edit_frame_btn.setEnabled(True)
        else:
            self.selected_frame = None
            if hasattr(self, "edit_frame_btn"):
                self.edit_frame_btn.setEnabled(False)

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
        screenshot_count = len(screenshots)
        self.screenshots_count_label.setText(str(screenshot_count))
        logger.debug(
            f"Updated screenshot count display: {screenshot_count} screenshots for {self.selected_frame.get('name')}"
        )

        # Regions
        regions = self.selected_frame.get("regions", {})
        text_regions = regions.get("text", [])
        text_region_count = len([r for r in text_regions if r.get("text", "").strip()])
        self.text_regions_label.setText(str(text_region_count))

        interact_regions = regions.get("interact", [])
        interact_region_count = len(interact_regions)
        self.interact_regions_label.setText(str(interact_region_count))

        # _manage_screenshots removed: ScreenshotManager is now launched from MainOverlay only.

    def _edit_selected_frame(self):
        """Edit the selected frame."""
        if not self.selected_frame:
            QMessageBox.warning(self, "Error", "Please select a frame first")
            return

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
                    # Update selected_frame to the latest database version
                    self.selected_frame = frame_data.copy()
                    break

        self._on_frame_selected()

    def check_for_updates(self):
        """Check if frames data needs to be refreshed based on global update signals."""
        try:
            import time
            from utility.update_manager import UpdateManager

            update_manager = UpdateManager.instance()
            if update_manager.needs_update("frames_data", self.last_frames_check):
                logger.debug("Global frames data update detected, refreshing...")

                # Save current selection name
                current_frame_name = None
                if self.selected_frame:
                    current_frame_name = self.selected_frame.get("name")

                # Force refresh frames list from database
                self._refresh_frames_list()

                # If we had a selection, get the fresh data from database
                if current_frame_name:
                    fresh_frame = self.frames_management.get_frame_by_name(current_frame_name)
                    if fresh_frame:
                        self.selected_frame = fresh_frame.copy()
                        logger.debug(
                            f"Updated selected_frame with fresh data: {len(fresh_frame.get('screenshots', []))} screenshots"
                        )

                # Update the display with fresh data
                self._update_frame_display()
                self.last_frames_check = time.time()
                return True
            return False
        except Exception as e:
            logger.warning(f"Failed to check for global updates: {e}")
            return False  # Compatibility methods for the main overlay

    def show_frames_dialog(self):
        """Show the frames dialog offset from the main overlay window."""
        try:
            # Offset from main overlay if possible
            if self.main_widget and hasattr(self.main_widget, "geometry"):
                main_geom = self.main_widget.geometry()
                x = main_geom.x() - 700
                y = main_geom.y() + 100
                self.move(x, y)

            # Check for updates before showing
            self.check_for_updates()

            self.show()
            self.activateWindow()
            self.raise_()

            # Use UpdatePoller for polling updates if needed (decoupled from QTimer)
            from utility.update_poller import UpdatePoller

            if not hasattr(self, "_update_poller"):
                self._update_poller = UpdatePoller(
                    "frames_data", self.check_for_updates, poll_interval=2000, parent=self
                )
            self._update_poller.start()

            logger.info("Frames dialog shown")
        except Exception as e:
            logger.error(f"Error showing frames dialog: {e}")

    def closeEvent(self, event):
        """Handle dialog close event to clean up timer."""
        if hasattr(self, "_update_poller"):
            self._update_poller.stop()
        super().closeEvent(event)

    def reject(self):
        """Handle dialog rejection to clean up timer."""
        if hasattr(self, "_update_poller"):
            self._update_poller.stop()
        super().reject()

    def accept(self):
        """Handle dialog acceptance to clean up timer."""
        if hasattr(self, "_update_poller"):
            self._update_poller.stop()
        super().accept()
