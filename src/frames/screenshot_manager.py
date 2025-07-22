"""
Screenshot Manager Dialog Widget

Screenshots save location: assets/screenshots
Screenshots filename: <frame_name>_<timestamp>_<uuid>.png

New screenshots are only to be taken of the "playable area"

- Nothing is finalized until "Save" is clicked
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
        self.frame_data = frame_data.copy()  # Always work on a copy
        self.frames_manager = frames_manager
        self.parent_widget = parent_widget  # Store reference to parent widget for screenshot capture
        self.logger = logging.getLogger(__name__)

        # State management
        self.current_screenshots = frame_data.get("screenshots", []).copy()  # UUIDs for gallery
        self.staged_screenshots = []  # List of dicts: {uuid, temp_path, action, is_primary}
        self.primary_uuid = self.current_screenshots[0] if self.current_screenshots else None
        self.selected_uuids = set()  # UUIDs of selected screenshots

        self.setWindowTitle(f"Screenshot Manager - {frame_data.get('name', 'Unnamed')}")
        self.setModal(True)
        self.resize(900, 500)

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

        self.new_screenshot_button = QPushButton("Add Screenshot")
        self.new_screenshot_button.clicked.connect(self._add_screenshot)

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

        self.screenshots_scroll.setWidget(self.screenshots_widget)
        layout.addWidget(self.screenshots_scroll)

        # Dialog buttons (bottom)
        dialog_button_layout = QHBoxLayout()
        dialog_button_layout.addStretch()

        self.save_button = QPushButton("Save")
        self.save_button.clicked.connect(self._save_changes)
        self.save_button.setEnabled(False)  # Only enabled if there are staged changes

        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.clicked.connect(self._cancel_changes)

        dialog_button_layout.addWidget(self.save_button)
        dialog_button_layout.addWidget(self.cancel_button)
        layout.addLayout(dialog_button_layout)

        # set cancel as default button
        self.cancel_button.setDefault(True)

        # Now that all buttons are created, display screenshots
        self._screenshots_display()

    def _cancel_changes(self):
        """Clean up staged screenshots and close dialog."""
        for staged in self.staged_screenshots:
            if staged["action"] == "add":
                try:
                    if staged["temp_path"].exists():
                        staged["temp_path"].unlink()
                        self.logger.info(f"Deleted temp screenshot {staged['temp_path']}")
                except Exception as e:
                    self.logger.warning(f"Failed to delete temp screenshot {staged['temp_path']}: {e}")
        self.staged_screenshots.clear()
        self.reject()

    def _save_changes(self):
        """Finalize staged screenshots: update DB via DatabaseManagement instance, move/delete files as needed."""
        from shutil import move

        db = getattr(self.frames_manager, "frames_management", None)
        if db is None:
            try:
                from frames.utility.database_management import DatabaseManagement

                db = DatabaseManagement(Path("."))
            except Exception as e:
                QMessageBox.warning(self, "Error", f"Could not get database manager: {e}")
                return
        screenshots_dir = self.frames_manager.screenshots_dir
        frame_name = self.frame_data.get("name")
        # Work on a copy of frame_data
        frame_data = self.frame_data.copy()
        screenshots = frame_data.get("screenshots", []).copy()
        # Apply staged actions
        for staged in self.staged_screenshots:
            if staged["action"] == "add":
                final_path = screenshots_dir / staged["temp_path"].name
                try:
                    move(str(staged["temp_path"]), final_path)
                    screenshots.append(staged["uuid"])
                    self.logger.info(f"Moved screenshot to {final_path}")
                except Exception as e:
                    self.logger.error(f"Failed to move screenshot {staged['temp_path']} to {final_path}: {e}")
            elif staged["action"] == "delete":
                try:
                    if staged["uuid"] in screenshots:
                        screenshots.remove(staged["uuid"])
                    db.delete_screenshot(staged["uuid"])
                    self.logger.info(f"Deleted screenshot {staged['uuid']}")
                except Exception as e:
                    self.logger.error(f"Failed to delete screenshot {staged['uuid']}: {e}")
        # Set primary if needed
        primary_uuid = None
        for s in self.staged_screenshots:
            if s.get("is_primary"):
                primary_uuid = s["uuid"]
        if primary_uuid:
            frame_data["primary_screenshot"] = primary_uuid
        frame_data["screenshots"] = screenshots
        # Update frame in DB
        db.update_frame(frame_name, frame_data)
        self.staged_screenshots.clear()

        # Update self.frame_data so parent can retrieve latest
        self.frame_data = frame_data.copy()

        # Signal global update
        try:
            from utility.update_manager import UpdateManager

            UpdateManager.instance().signal_update("frames_data", "screenshot_manager")
        except Exception as e:
            self.logger.warning(f"Failed to signal global update: {e}")

        self.accept()

    def _screenshots_display(self):
        """Display screenshots in a 4-column grid as 192x128 thumbnails, with selection and temp support."""
        # Clear existing widgets from the grid
        for i in reversed(range(self.screenshots_layout.count())):
            item = self.screenshots_layout.itemAt(i)
            if item and item.widget():
                widget = item.widget()
                if widget:
                    widget.setParent(None)

        row, col = 0, 0
        max_cols = 4
        thumb_width, thumb_height = 192, 128

        # Build a map of staged temp files for display
        staged_temp_map = {s["uuid"]: s["temp_path"] for s in self.staged_screenshots if s["action"] == "add"}
        staged_delete = {s["uuid"] for s in self.staged_screenshots if s["action"] == "delete"}

        for idx, uuid in enumerate(self.current_screenshots):
            if uuid in staged_delete:
                continue  # Don't show deleted
            # Find the screenshot file by UUID, prefer temp if staged
            screenshot_path = None
            if uuid in staged_temp_map:
                screenshot_path = staged_temp_map[uuid]
            else:
                for file_path in self.frames_manager.screenshots_dir.glob(f"*{uuid}*.png"):
                    screenshot_path = file_path
                    break

            from PyQt6.QtGui import QMouseEvent

            class ClickableLabel(QLabel):
                def __init__(self, uuid, dialog, parent=None):
                    super().__init__(parent)
                    self.uuid = uuid
                    self.dialog = dialog

                def mousePressEvent(self, ev: "QMouseEvent"):
                    if ev.button() == Qt.MouseButton.LeftButton:
                        if self.uuid in self.dialog.selected_uuids:
                            self.dialog.selected_uuids.remove(self.uuid)
                        else:
                            self.dialog.selected_uuids.add(self.uuid)
                        self.dialog._update_action_buttons()
                        self.dialog._screenshots_display()

            label = ClickableLabel(uuid, self)
            label.setFixedSize(thumb_width, thumb_height)
            label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            # Border highlight: green for primary, blue for selection, both if primary and selected
            if idx == 0 and uuid in self.selected_uuids:
                # Both primary and selected: double border (green outer, blue inner)
                border_style = "border: 4px solid #0078d7; border-radius: 6px"
            elif idx == 0:
                # Primary screenshot: green border
                border_style = "border: 2px solid #2ecc40; border-radius: 6px;"
            elif uuid in self.selected_uuids:
                border_style = "border: 4px solid #0078d7; border-radius: 6px;"
            else:
                border_style = ""
            label.setStyleSheet(border_style)
            # Show image or missing
            if screenshot_path and screenshot_path.exists():
                pixmap = QPixmap(str(screenshot_path))
                if not pixmap.isNull():
                    scaled = pixmap.scaled(
                        thumb_width,
                        thumb_height,
                        Qt.AspectRatioMode.KeepAspectRatio,
                        Qt.TransformationMode.SmoothTransformation,
                    )
                    label.setPixmap(scaled)
                else:
                    label.setText("Invalid\nImage")
                    label.setStyleSheet("color: red;" if not border_style else border_style + "color: red;")
            else:
                label.setText("Missing\nFile")
                label.setStyleSheet("color: red;" if not border_style else border_style + "color: red;")
            self.screenshots_layout.addWidget(label, row, col)
            col += 1
            if col >= max_cols:
                col = 0
                row += 1

        if not self.current_screenshots or all(u in staged_delete for u in self.current_screenshots):
            no_screenshots_label = QLabel("No screenshots available")
            no_screenshots_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.screenshots_layout.addWidget(no_screenshots_label, 0, 0)

        self._update_action_buttons()

    def _update_action_buttons(self):
        # Only allow make primary if exactly 1 selected and not already primary
        if len(self.selected_uuids) == 1:
            selected_uuid = next(iter(self.selected_uuids))
            is_primary = self.current_screenshots and selected_uuid == self.current_screenshots[0]
            self.make_primary_button.setEnabled(not is_primary)
            # Don't allow delete if primary is selected
            self.delete_button.setEnabled(not is_primary)
        elif len(self.selected_uuids) > 0:
            self.make_primary_button.setEnabled(False)
            # Don't allow delete if primary is selected
            if self.current_screenshots and self.current_screenshots[0] in self.selected_uuids:
                self.delete_button.setEnabled(False)
            else:
                self.delete_button.setEnabled(True)
        else:
            self.make_primary_button.setEnabled(False)
            self.delete_button.setEnabled(False)

        # Enable Save only if there are staged changes
        if self.staged_screenshots:
            self.save_button.setEnabled(True)
        else:
            self.save_button.setEnabled(False)

    def _make_primary(self):
        # Only allow if exactly 1 selected and not already primary
        if len(self.selected_uuids) != 1 or not self.current_screenshots:
            return
        selected_uuid = next(iter(self.selected_uuids))
        if selected_uuid == self.current_screenshots[0]:
            return  # Already primary
        # Stage the primary change: move selected to front on save
        for s in self.staged_screenshots:
            s["is_primary"] = s["uuid"] == selected_uuid
        self.primary_uuid = selected_uuid
        self._update_action_buttons()
        self._screenshots_display()

    def _delete_selected(self):
        # Only allow if at least one selected and none is primary
        if not self.selected_uuids:
            return
        if self.current_screenshots and self.current_screenshots[0] in self.selected_uuids:
            return  # Don't allow deleting primary
        for uuid in list(self.selected_uuids):
            if uuid in self.current_screenshots:
                # Mark for delete if staged add, else add staged delete
                found = False
                for s in self.staged_screenshots:
                    if s["uuid"] == uuid:
                        s["action"] = "delete"
                        found = True
                if not found:
                    self.staged_screenshots.append(
                        {"uuid": uuid, "temp_path": None, "action": "delete", "is_primary": False}
                    )
                self.current_screenshots.remove(uuid)
        self.selected_uuids.clear()
        self._update_action_buttons()
        self._screenshots_display()

    def _add_screenshot(self):
        """Capture the playable area, stage screenshot in temp, and update gallery. No DB update until Save."""
        import uuid
        from datetime import datetime

        try:
            from utility.window_utils import find_target_window
            from PIL import ImageGrab
            import win32gui
            import win32con
            import time
            from PyQt6.QtWidgets import QApplication
        except ImportError as e:
            self.logger.error(f"Required modules not found: {e}")
            QMessageBox.warning(self, "Error", f"Required modules not found: {e}")
            return

        # --- Find target window and playable area ---
        target_info = find_target_window("WidgetInc.exe")
        self.logger.debug(f"Target window info: {target_info}")
        if not target_info or not target_info.get("window_info"):
            self.logger.error(f"Could not find WidgetInc.exe or its window. target_info={target_info}")
            return
        area = target_info.get("playable_area")
        if not area:
            self.logger.error(f"Could not find absolute playable area in target_info: {target_info}")
            return
        x, y, w, h = area["x"], area["y"], area["width"], area["height"]
        self.logger.debug(f"Playable area (absolute): x={x}, y={y}, w={w}, h={h}")

        hwnd = target_info["window_info"]["hwnd"]
        current_foreground = win32gui.GetForegroundWindow()

        # --- Helper: minimize and restore tools ---
        from PyQt6.QtWidgets import QWidget

        def get_tools_to_minimize() -> list[QWidget]:
            tools: list[QWidget] = [self]
            parent = self.parent() if hasattr(self, "parent") and self.parent() else None
            if isinstance(parent, QWidget) and hasattr(parent, "showMinimized"):
                tools.append(parent)
                self.logger.debug(f"Added parent to minimize: {parent}")
            if isinstance(self.parent_widget, QWidget) and hasattr(self.parent_widget, "showMinimized"):
                tools.append(self.parent_widget)
                self.logger.debug(f"Added main overlay to minimize: {self.parent_widget}")
            return tools

        tools_to_minimize = get_tools_to_minimize()

        def minimize_tools():
            for tool in tools_to_minimize:
                try:
                    tool.showMinimized()
                    self.logger.debug(f"Minimized tool: {tool}")
                except Exception as e:
                    self.logger.warning(f"Failed to minimize tool {tool}: {e}")
            QApplication.processEvents()
            time.sleep(0.3)

        def restore_tools():
            for tool in tools_to_minimize:
                try:
                    tool.showNormal()
                    tool.raise_()
                    tool.activateWindow()
                    self.logger.debug(f"Restored tool from minimized: {tool}")
                except Exception as e:
                    self.logger.warning(f"Failed to restore tool {tool}: {e}")
            QApplication.processEvents()

        # --- Minimize tools, bring game to front, capture screenshot, restore tools ---
        screenshot = None
        frame_name = self.frame_data.get("name", "unnamed").replace(" ", "_")
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        screenshot_uuid = str(uuid.uuid4())
        temp_dir = Path("assets/screenshots/temp")
        temp_dir.mkdir(parents=True, exist_ok=True)
        temp_filename = f"{frame_name}_{timestamp}_{screenshot_uuid}.temp.png"
        temp_path = temp_dir / temp_filename
        try:
            minimize_tools()
            # Bring target window to foreground
            try:
                win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
                win32gui.ShowWindow(hwnd, win32con.SW_SHOW)
                win32gui.SetWindowPos(
                    hwnd,
                    win32con.HWND_TOP,
                    0,
                    0,
                    0,
                    0,
                    win32con.SWP_NOMOVE | win32con.SWP_NOSIZE | win32con.SWP_SHOWWINDOW,
                )
                win32gui.SetForegroundWindow(hwnd)
                win32gui.BringWindowToTop(hwnd)
                self.logger.debug("Target window brought to foreground with multiple methods")
            except Exception as e:
                self.logger.warning(f"Failed to bring target window to foreground: {e}")
            QApplication.processEvents()
            time.sleep(0.8)
            screenshot = ImageGrab.grab(bbox=(x, y, x + w, y + h), all_screens=True)
            self.logger.debug(f"Screenshot captured: size={screenshot.size}, mode={screenshot.mode}")
            screenshot.save(temp_path)
            self.logger.info(f"Screenshot saved to {temp_path}")
        except Exception as e:
            self.logger.error(f"Failed to capture/save screenshot: {e}")
            QMessageBox.warning(self, "Error", f"Failed to capture/save screenshot: {e}")
            return
        finally:
            restore_tools()
            try:
                if current_foreground and current_foreground != hwnd:
                    win32gui.SetForegroundWindow(current_foreground)
            except Exception as e:
                self.logger.warning(f"Failed to restore original foreground window: {e}")
            try:
                self.raise_()
                self.activateWindow()
            except Exception as e:
                self.logger.warning(f"Failed to restore screenshot manager to front: {e}")

        if not screenshot:
            self.logger.error("Screenshot capture failed - no image data")
            return

        # Stage the screenshot (not finalized)
        self.staged_screenshots.append(
            {"uuid": screenshot_uuid, "temp_path": temp_path, "action": "add", "is_primary": False}
        )
        self.current_screenshots.append(screenshot_uuid)
        self._screenshots_display()
