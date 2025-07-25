import json
import logging
import os
import re
import sys
from collections import defaultdict
from pathlib import Path

from PyQt6.QtCore import Qt, QTimer
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

from utility.window_utils import find_target_window, calculate_overlay_position


def setup_logging():
    """Setup logging configuration based on command line arguments."""
    # Check if debug argument is passed
    debug_mode = "--debug" in sys.argv or "-d" in sys.argv

    # Create logs directory
    logs_dir = Path(__file__).parent.parent / "logs"
    logs_dir.mkdir(exist_ok=True)

    # Configure logging level
    log_level = logging.DEBUG if debug_mode else logging.INFO

    # Setup logging format
    log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

    # Configure root logger
    logging.basicConfig(
        level=log_level,
        format=log_format,
        handlers=[logging.FileHandler(logs_dir / "automation_overlay.log"), logging.StreamHandler(sys.stdout)],
    )

    logger = logging.getLogger(__name__)
    logger.info(f"Starting Widget Automation Tool - Debug mode: {debug_mode}")
    return logger


class CustomTitleBar(QWidget):
    """Custom title bar with minimize and close buttons."""

    def __init__(self, parent):
        super().__init__(parent)
        self.main_window = parent
        self.logger = logging.getLogger(f"{__name__}.CustomTitleBar")
        self.logger.debug("Initializing custom title bar")
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


class MainWindow(QMainWindow):
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

    def __init__(self):
        super().__init__()
        self.logger = logging.getLogger(f"{__name__}.MainWindow")
        self.logger.info("Initializing main window")

        self.setWindowTitle("Widget Automation Tool")
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint | Qt.WindowType.Window
        )
        self.setMinimumSize(100, 200)  # Set a reasonable minimum size
        self.logger.debug("Window flags and size configured")

        # Initialize window snapping
        self.setup_window_snapping()

        # Load frames from JSON (adjusted path for our project structure)
        frames_file = Path(__file__).parent / "config" / "frames_database.json"
        self.logger.debug(f"Loading frames from: {frames_file}")
        try:
            with open(frames_file, "r", encoding="utf-8") as f:
                frames_data = json.load(f)
            frames = frames_data.get("frames", [])
            self.logger.info(f"Loaded {len(frames)} frames from database")
        except FileNotFoundError:
            self.logger.error(f"Could not find frames database at {frames_file}")
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
            # Tier header
            tier_label = QLabel(f"TIER {tier}")
            tier_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            content_layout.addWidget(tier_label)
            self.logger.debug(f"Created tier {tier} with {len(tiers[tier])} frames")

            # Buttons for this tier
            row_widget = QWidget()
            row_layout = QVBoxLayout(row_widget)
            row_layout.setSpacing(8)
            row_layout.setContentsMargins(8, 0, 0, 0)

            for frame in tiers[tier]:
                btn = self.create_frame_button(frame)
                row_layout.addWidget(btn)
            content_layout.addWidget(row_widget)

        # Scroll area for content
        scroll = QScrollArea()
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

        # Auto-resize width to fit content, allow manual resizing
        self.adjustSize()
        # Set width to fit contents
        content_width = content_container.sizeHint().width() + 15  # Add padding for scroll area and layout
        self.resize(content_width, self.height())  # Resize only width, keep current height
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

        # Don't set initial position here - let window snapping handle it
        # self.move(100, 100)  # Removed - this was overriding the snap positioning

        self.logger.info(f"Window initialized with size: {self.width()}x{self.height()}")

    def setup_window_snapping(self):
        """Setup window snapping to WidgetInc application."""
        self.logger.debug("Setting up window snapping")
        # Track last position to avoid spam logging
        self.last_snap_position = None
        # Timer for periodic window detection and snapping
        self.snap_timer = QTimer(self)
        self.snap_timer.timeout.connect(self.check_and_snap_to_window)
        self.snap_timer.start(1000)  # Check every second

        # Initial snap attempt
        self.check_and_snap_to_window()

    def check_and_snap_to_window(self):
        """Check for WidgetInc window and snap overlay to it."""
        try:
            target_info = find_target_window()
            if target_info and target_info.get("window_info"):
                window_info = target_info["window_info"]

                # Use the calculate_overlay_position function for cleaner positioning
                overlay_x, overlay_y, available_height = calculate_overlay_position(
                    window_info=window_info,
                    overlay_width=self.width(),
                    overlay_height=self.height(),
                )

                # Only log and move if position changed
                current_position = (overlay_x, overlay_y)
                self.resize(self.width(), available_height)
                if self.last_snap_position != current_position:
                    self.move(overlay_x, overlay_y)
                    self.logger.debug(f"Snapped overlay to WidgetInc window at position: {overlay_x}, {overlay_y}")
                    self.last_snap_position = current_position
            else:
                # Only log "not found" once when it changes state
                if self.last_snap_position is not None:
                    self.logger.debug("WidgetInc window not found for snapping")
                    self.last_snap_position = None

        except Exception as e:
            self.logger.debug(f"Error during window snapping: {e}")
            # Silently ignore errors - window might not be available
            pass

    def create_frame_button(self, frame):
        """Create a button for a frame with automation status styling."""
        name = frame.get("name", "Unknown")
        automation = frame.get("automation", 0)
        frame_id = frame.get("id", "")

        # Safe logging that handles emojis by encoding them as text
        safe_name = name.encode("ascii", "replace").decode("ascii")
        self.logger.debug(f"Creating button for frame: {safe_name} (ID: {frame_id}, Automation: {automation})")

        btn = QPushButton(name)
        btn.setToolTip(f"ID: {frame_id}\nAutomation: {'Available' if automation else 'Not Implemented'}")

        # Only minimal font styling as per copilot instructions
        btn.setStyleSheet("""
            QPushButton {
                font-family: 'Noto Sans', 'Segoe UI';
                font-size: 12px;
            }
        """)

        # Connect button click to automation
        btn.clicked.connect(lambda checked, f=frame: self.start_automation(f))

        return btn

    def start_automation(self, frame):
        """Handle frame automation start."""
        name = frame.get("name", "Unknown")
        automation = frame.get("automation", 0)
        frame_id = frame.get("id", "")

        # Safe logging that handles emojis by encoding them as text
        safe_name = name.encode("ascii", "replace").decode("ascii")

        if automation:
            self.logger.info(f"Starting automation for: {safe_name} (ID: {frame_id})")
            print(f"🤖 Starting automation for: {name} (ID: {frame_id})")
            # TODO: Implement actual automation logic here
        else:
            self.logger.info(f"Automation not implemented for: {safe_name} (ID: {frame_id})")
            print(f"⚠️  Automation not implemented for: {name} (ID: {frame_id})")


def main():
    # Setup logging first
    logger = setup_logging()

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
