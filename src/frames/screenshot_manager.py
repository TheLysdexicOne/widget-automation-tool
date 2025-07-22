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
        self.frame_data = frame_data
        self.frames_manager = frames_manager
        self.parent_widget = parent_widget  # Store reference to parent widget for screenshot capture
        self.logger = logging.getLogger(__name__)

        # State management
        self.current_screenshots = frame_data.get("screenshots", []).copy()

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

        self._screenshots_display()

        self.screenshots_scroll.setWidget(self.screenshots_widget)
        layout.addWidget(self.screenshots_scroll)

        # Dialog buttons (bottom)
        dialog_button_layout = QHBoxLayout()
        dialog_button_layout.addStretch()

        save_button = QPushButton("Save")
        save_button.clicked.connect(self._save_changes)
        save_button.setEnabled(False)

        cancel_button = QPushButton("Cancel")
        cancel_button.clicked.connect(self._cancel_changes)

        dialog_button_layout.addWidget(save_button)
        dialog_button_layout.addWidget(cancel_button)
        layout.addLayout(dialog_button_layout)

        # set cancel as default button
        cancel_button.setDefault(True)

    def _cancel_changes(self):
        """Cancel all changes and close dialog."""
        self.reject()

    def _save_changes(self):
        return

    def _screenshots_display(self):
        """Display screenshots in a 4-column grid as 192x128 thumbnails."""
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

        for uuid in self.current_screenshots:
            # Find the screenshot file by UUID
            screenshot_path = None
            for file_path in self.frames_manager.screenshots_dir.glob(f"*{uuid}*.png"):
                screenshot_path = file_path
                break

            label = QLabel()
            label.setFixedSize(thumb_width, thumb_height)
            label.setAlignment(Qt.AlignmentFlag.AlignCenter)

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
                    label.setStyleSheet("color: red;")
            else:
                label.setText("Missing\nFile")
                label.setStyleSheet("color: red;")

            self.screenshots_layout.addWidget(label, row, col)
            col += 1
            if col >= max_cols:
                col = 0
                row += 1

        if not self.current_screenshots:
            no_screenshots_label = QLabel("No screenshots available")
            no_screenshots_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.screenshots_layout.addWidget(no_screenshots_label, 0, 0)

    def _make_primary(self):
        return

    def _delete_selected(self):
        return

    def _add_screenshot(self):
        """Capture the playable area of WidgetInc.exe using PIL ImageGrab with all_screens=True. Minimize tool windows, bring game to front, capture, then restore tools."""
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
        except Exception as e:
            self.logger.error(f"Failed to capture screenshot: {e}")
            QMessageBox.warning(self, "Error", f"Failed to capture screenshot: {e}")
            return
        finally:
            restore_tools()
            # Try to restore original foreground window (optional)
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

        # Save screenshot to temp folder using naming convention: <frame_name>_<timestamp>_<uuid>.png
        import uuid
        from datetime import datetime

        temp_dir = Path("assets/screenshots/temp")
        temp_dir.mkdir(parents=True, exist_ok=True)
        frame_name = self.frame_data.get("name", "unnamed").replace(" ", "_")
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        screenshot_uuid = str(uuid.uuid4())
        temp_filename = f"{frame_name}_{timestamp}_{screenshot_uuid}.png"
        temp_path = temp_dir / temp_filename
        try:
            screenshot.save(temp_path)
            self.logger.info(f"Screenshot saved to {temp_path}")
        except Exception as e:
            self.logger.error(f"Failed to save screenshot to {temp_path}: {e}")
            QMessageBox.warning(self, "Error", f"Failed to save screenshot: {e}")
