import json
import logging
import os
import re
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any, Dict

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QApplication,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QMenu,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from automation.automation_controller import AutomationController
from automation.global_hotkey_manager import GlobalHotkeyManager
from utility.window_manager import get_window_manager
from utility.coordinate_utils import generate_db_cache
from utility.logging_utils import setup_logging, LoggerMixin


class CustomTitleBar(QWidget, LoggerMixin):
    """Custom title bar with minimize and close buttons."""

    def __init__(self, parent):
        super().__init__(parent)
        self.main_window = parent
        self.logger = logging.getLogger(self.__class__.__name__)
        self.log_debug("Initializing custom title bar")
        self.setFixedHeight(30)

        # Create layout
        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 0, 0, 0)
        layout.setSpacing(0)

        # Title label
        self.title_label = QLabel("Widgets Automation")

        # Spacer
        layout.addWidget(self.title_label)
        layout.addStretch()

        # Minimize button
        self.minimize_btn = QPushButton("−")
        self.minimize_btn.setFixedSize(30, 30)
        self.minimize_btn.clicked.connect(self.main_window.showMinimized)

        # Close button
        self.close_btn = QPushButton("×")
        self.close_btn.setFixedSize(30, 30)
        self.close_btn.clicked.connect(self.main_window.close)

        layout.addWidget(self.minimize_btn)
        layout.addWidget(self.close_btn)


class MainWindow(QMainWindow, LoggerMixin):
    def __init__(self):
        super().__init__()
        self.logger = logging.getLogger(self.__class__.__name__)
        self.log_info("Initializing main window")

        # Initialize automation controller and global hotkeys
        self.automation_controller = AutomationController()
        self.automation_controller.set_ui_callback(self.handle_automation_event)
        self.automation_controller.set_completion_callback(self.handle_automation_completion)
        self.hotkey_manager = GlobalHotkeyManager()
        self.hotkey_manager.set_stop_callback(self.stop_all_automations)

        # Initialize WindowManager and connect signals
        self.window_manager = get_window_manager()
        self.window_manager.window_found.connect(self.on_window_found)
        self.window_manager.window_lost.connect(self.on_window_lost)

        # Track button states for toggle functionality
        self.automation_buttons = {}  # frame_id -> button mapping

        self.setWindowTitle("Widget Automation Tool")
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint | Qt.WindowType.Window
        )
        self.setMinimumSize(100, 200)  # Set a reasonable minimum size
        self.log_debug("Window flags and size configured")

        # Disable context menu to prevent interference with right-click hotkey
        self.setContextMenuPolicy(Qt.ContextMenuPolicy.NoContextMenu)

        # Initialize window snapping
        self.setup_window_snapping()
        generate_db_cache()

        # Load frames from converted cache (screen coordinates)
        frames_file = Path(__file__).parent.parent / "config" / "database" / "frames.json"
        self.logger.debug(f"Loading frames from: {frames_file}")
        try:
            with open(frames_file, "r", encoding="utf-8") as f:
                frames_data = json.load(f)
            frames = frames_data.get("frames", [])
            self.logger.info(f"Loaded {len(frames)} frames from database")
        except FileNotFoundError:
            self.log_error(f"Could not find frames database at {frames_file}")
            print(f"Warning: Could not find frames database at {frames_file}")
            frames = []

        # Group frames by tier
        tiers = defaultdict(list)
        for frame in frames:
            match = re.match(r"(\d+)\.\d+", frame.get("id", ""))
            if match:
                tier = int(match.group(1))
            else:
                tier = 0
            tiers[tier].append(frame)

        self.logger.debug(f"Grouped frames into {len(tiers)} tiers: {sorted(tiers.keys())}")

        # Create main widget with custom title bar
        main_widget = QWidget()
        main_layout = QVBoxLayout(main_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Add custom title bar
        self.title_bar = CustomTitleBar(self)
        main_layout.addWidget(self.title_bar)
        self.logger.debug("Created custom title bar")

        # Create title widget
        self.title_label = QLabel("WIDGETS")
        self.title_label.setSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Minimum)
        self.title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.title_label.setStyleSheet("""
            QLabel {
            font-size: 18px;
            font-weight: bold;
            }
        """)

        # Main content widget
        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)
        content_layout.setSpacing(8)
        content_layout.setContentsMargins(4, 4, 4, 4)

        for tier in sorted(tiers.keys()):
            # Collect buttons for this tier first to check if any will be created
            tier_buttons = []
            for frame in tiers[tier]:
                btn = self.create_frame_button(frame)
                if btn is not None:  # Only collect created buttons
                    tier_buttons.append(btn)

            # Only create tier section if there are buttons to show
            if tier_buttons:
                # Tier header
                tier_label = QLabel(f"TIER {tier}")
                tier_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
                content_layout.addWidget(tier_label)
                self.logger.debug(f"Created tier {tier} with {len(tier_buttons)} buttons")

                # Buttons for this tier
                row_widget = QWidget()
                row_layout = QVBoxLayout(row_widget)
                row_layout.setSpacing(8)
                row_layout.setContentsMargins(8, 0, 0, 0)

                for btn in tier_buttons:
                    row_layout.addWidget(btn)
                content_layout.addWidget(row_widget)
            else:
                self.logger.debug(f"Skipping tier {tier} - no automatable frames")

        # Scroll area for content
        scroll = QScrollArea()
        # Enable vertical scroll bar and allow overscroll
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOn)
        scroll.setWidgetResizable(True)
        scroll.setWidget(content_widget)

        # Layout
        content_container_layout = QVBoxLayout()
        content_container_layout.addWidget(self.title_label)
        content_container_layout.addWidget(scroll)

        content_container = QWidget()
        content_container.setLayout(content_container_layout)

        main_layout.addWidget(content_container)

        self.setCentralWidget(main_widget)

        # Calculate content size first
        content_container.adjustSize()
        self.adjustSize()

        # Get preferred content dimensions
        preferred_width = content_container.sizeHint().width() + 15  # Add padding for scroll area
        preferred_height = content_container.sizeHint().height() + self.title_bar.height()

        # Set initial size to preferred content size
        self.resize(preferred_width, preferred_height)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

        self.logger.info(f"Window initialized with preferred size: {preferred_width}x{preferred_height}")

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.RightButton:
            self.logger.debug("Right-click detected, showing context menu")
            pos = event.position().toPoint() if hasattr(event, "position") else event.pos()
            widget = self.childAt(pos)

            if isinstance(widget, QPushButton):
                return
            menu = QMenu(self)
            restart_action = menu.addAction("Restart")
            menu.addSeparator()
            exit_action = menu.addAction("Exit")
            global_pos = event.globalPosition().toPoint() if hasattr(event, "globalPosition") else event.globalPos()
            action = menu.exec(global_pos)
            if action == restart_action:
                self.restart_app()
            elif action == exit_action:
                self.close()
        else:
            super().mousePressEvent(event)

    def restart_app(self):
        self.logger.info("Restarting application")
        # Relaunch the current script
        os.execv(sys.executable, [sys.executable] + sys.argv)

    def closeEvent(self, event):
        """Handle window closing - ensure cleanup."""
        self.logger.info("Application closing - cleaning up")

        # Stop hotkey monitoring
        self.hotkey_manager.stop_monitoring()

        # Stop all automations
        self.automation_controller.stop_all_automations()

        # Accept the close event
        event.accept()

    def setup_window_snapping(self):
        """Setup window snapping to WidgetInc application."""
        self.logger.debug("Setting up window snapping")
        # Track last position to avoid spam logging
        self.last_snap_position = None

        # WindowManager will notify us of changes automatically via signals
        # No need for manual timer - much more efficient!

        # Initial snap attempt
        self.check_and_snap_to_window()

    def check_and_snap_to_window(self):
        """Check for WidgetInc window and snap overlay to it."""
        try:
            # Use WindowManager to get cached overlay position
            window_manager = get_window_manager()
            overlay_position = window_manager.get_overlay_position()

            if overlay_position:
                overlay_x = overlay_position["x"]
                overlay_y = overlay_position["y"]
                available_height = overlay_position["available_height"]

                # Calculate optimal height: smaller of content size or available space
                central_widget = self.centralWidget()
                if central_widget:
                    content_height = central_widget.sizeHint().height()
                    optimal_height = min(content_height, available_height)
                else:
                    optimal_height = available_height

                # Only log and move if position changed
                current_position = (overlay_x, overlay_y)
                if self.last_snap_position != current_position:
                    self.move(overlay_x, overlay_y)
                    self.resize(self.width(), optimal_height)
                    self.logger.debug(
                        f"Snapped overlay to WidgetInc window at position: {overlay_x}, {overlay_y} (height: {optimal_height})"
                    )
                    self.last_snap_position = current_position
                    generate_db_cache()

                elif self.height() != optimal_height:
                    # Update height even if position hasn't changed
                    self.resize(self.width(), optimal_height)
            else:
                # Only log "not found" once when it changes state
                if self.last_snap_position is not None:
                    self.logger.debug("WidgetInc window not found for snapping")
                    self.last_snap_position = None

        except Exception as e:
            self.logger.debug(f"Error during window snapping: {e}")
            # Silently ignore errors - window might not be available
            pass

    def on_window_found(self, window_info: Dict[str, Any]):
        """Handle WindowManager window_found signal."""
        self.logger.debug("WindowManager detected window change - updating position")
        # Trigger immediate position update
        self.check_and_snap_to_window()

    def on_window_lost(self):
        """Handle WindowManager window_lost signal."""
        self.logger.debug("WindowManager detected window lost")
        self.last_snap_position = None

    def create_frame_button(self, frame):
        """Create a button for a frame with automation status styling."""
        name = frame.get("name", "Unknown")
        automation = frame.get("automation", {})
        frame_id = frame.get("id", "")
        item = frame.get("item", "")

        # Extract automation flags
        can_automate = automation.get("can_automate", 0) if isinstance(automation, dict) else automation
        programmed = automation.get("programmed", 0) if isinstance(automation, dict) else automation

        # Safe logging that handles emojis by encoding them as text
        safe_name = name.encode("ascii", "replace").decode("ascii")
        self.logger.debug(
            f"Creating button for frame: {safe_name} (ID: {frame_id}, Can Automate: {can_automate}, Programmed: {programmed})"
        )

        # Skip button creation if automation is not possible
        if not can_automate:
            self.logger.debug(f"Skipping button for {safe_name} - automation not possible")
            return None

        # Create button with appropriate text and functionality
        if programmed:
            btn = QPushButton(name)
            tooltip = f"ID: {frame_id}\nItem: {item}\nAutomation: Ready"
            # Connect to actual automation
            btn.clicked.connect(lambda checked, f=frame: self.toggle_automation(f))
            # Store button reference for state tracking
            self.automation_buttons[frame_id] = btn
            # Standard button styling (no extra CSS needed)
            button_style = """
            QPushButton {
                font-family: 'Noto Sans', 'Segoe UI';
                font-size: 12px;
            }
            """
        else:
            btn = QPushButton(name)  # Remove "(Not Programmed)" text
            tooltip = f"ID: {frame_id}\nItem: {item}\nAutomation: Not Implemented Yet"
            # Don't connect any click signal for unprogrammed buttons
            # Disable the button to show it's not ready
            btn.setEnabled(False)
            # Styling with explicit disabled state handling to prevent visual focus bugs
            button_style = """
            QPushButton {
                font-family: 'Noto Sans', 'Segoe UI';
                font-size: 12px;
            }
            """

        btn.setToolTip(tooltip)

        # Prevent spacebar from activating this button (interferes with global hotkey)
        btn.setFocusPolicy(Qt.FocusPolicy.NoFocus)

        # Apply styling
        btn.setStyleSheet(button_style)

        return btn

    def set_buttons_disabled(self, disabled: bool, exclude_frame_id: str | None = None):
        """Enable/disable all automation buttons, optionally excluding one."""
        for frame_id, button in self.automation_buttons.items():
            if exclude_frame_id and frame_id == exclude_frame_id:
                continue  # Skip the excluded button
            button.setEnabled(not disabled)

    def toggle_automation(self, frame):
        """Toggle automation start/stop for a frame."""
        frame_id = frame.get("id", "")

        # Check if automation is currently running
        if self.automation_controller.is_automation_running(frame_id):
            # Stop automation
            self.stop_automation(frame)
        else:
            # Start automation
            self.start_automation(frame)

    def stop_automation(self, frame):
        """Stop automation for a specific frame."""
        name = frame.get("name", "Unknown")
        frame_id = frame.get("id", "")

        safe_name = name.encode("ascii", "replace").decode("ascii")
        self.logger.info(f"Stopping automation for: {safe_name} (ID: {frame_id})")
        print(f"🛑 Stopping automation for: {name} (ID: {frame_id})")

        # Stop the specific automation
        success = self.automation_controller.stop_automation(frame_id)
        if success:
            self.log_info(f"Automation stopped successfully for: {safe_name}")
            print(f"✅ Automation stopped successfully for: {name}")
            # Re-enable all buttons when automation stops
            self.set_buttons_disabled(False)
        else:
            self.log_error(f"Failed to stop automation for: {safe_name}")
            print(f"❌ Failed to stop automation for: {name}")

    def start_automation(self, frame):
        """Handle frame automation start - only called for programmed automations."""
        name = frame.get("name", "Unknown")
        frame_id = frame.get("id", "")

        # Safe logging that handles emojis by encoding them as text
        safe_name = name.encode("ascii", "replace").decode("ascii")

        self.logger.info(f"Starting automation for: {safe_name} (ID: {frame_id})")
        print(f"🤖 Starting automation for: {name} (ID: {frame_id})")

        # Use automation controller to start automation
        success = self.automation_controller.start_automation(frame)
        if success:
            self.log_info(f"Automation started successfully for: {safe_name}")
            print(f"✅ Automation started successfully for: {name}")
            # Disable all buttons except the one running automation
            self.set_buttons_disabled(True, exclude_frame_id=frame_id)
            # Start global hotkey monitoring when automation starts
            self.hotkey_manager.start_monitoring()
        else:
            self.log_error(f"Failed to start automation for: {safe_name}")
            print(f"❌ Failed to start automation for: {name}")

    def handle_automation_completion(self, frame_id: str):
        """Handle automation completion (natural completion, not manual stop)."""
        self.logger.info(f"Automation completed naturally for frame: {frame_id}")

        # Stop hotkey monitoring
        self.hotkey_manager.stop_monitoring()

        # Re-enable all buttons
        self.set_buttons_disabled(False)

        self.log_info(f"Automation completed for frame: {frame_id}")
        print(f"✅ Automation completed for frame: {frame_id}")

    def handle_automation_event(self, event_type: str, frame_id: str, data: str | None = None):
        """Handle automation events from automators (failsafe, etc.)."""
        if event_type == "failsafe_stop":
            self.logger.warning(f"Failsafe triggered for {frame_id}: {data}")
            self.log_warning(f"Failsafe triggered for frame {frame_id}: {data}")
            print(f"🛑 Failsafe triggered for frame {frame_id}: {data}")

            # Re-enable all buttons immediately when failsafe is triggered
            self.set_buttons_disabled(False)

            # Stop hotkey monitoring since automation stopped
            self.hotkey_manager.stop_monitoring()

            self.log_info("Automation safely stopped and buttons re-enabled")
            print("✅ Automation safely stopped and buttons re-enabled")

    def stop_all_automations(self):
        """Stop all running automations (called by global hotkeys)."""
        self.logger.info("Stopping all automations via global hotkey")
        self.log_info("Stopping all automations (global hotkey detected)")
        print("🛑 Stopping all automations (global hotkey detected)")

        # Stop hotkey monitoring
        self.hotkey_manager.stop_monitoring()

        # Re-enable all buttons when all automations stop
        self.set_buttons_disabled(False)

        # Stop all automations
        self.automation_controller.stop_all_automations()

        self.log_info("All automations stopped")
        print("✅ All automations stopped")


def main():
    # Setup logging first
    setup_logging()

    # Use custom logger name instead of module name
    logger = logging.getLogger("Initialization")

    logger.info("Creating QApplication")
    app = QApplication(sys.argv)

    logger.info("Creating main window")
    window = MainWindow()
    window.show()

    logger.info("Application started successfully")
    try:
        return app.exec()
    except KeyboardInterrupt:
        logger.info("Application interrupted by user")
        print("\nApplication interrupted by user")
        app.quit()
        return 0
    except Exception as e:
        logger.error(f"Application error: {e}")
        print(f"Application error: {e}")
        app.quit()
        return 1


if __name__ == "__main__":
    sys.exit(main())
