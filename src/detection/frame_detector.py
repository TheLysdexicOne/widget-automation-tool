import logging
import json
import pickle
import os
from pathlib import Path
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtWidgets import QWidget, QPushButton

from utility.logging_utils import LoggerMixin


class FrameDetector(QWidget, LoggerMixin):
    """
    Frame detector overlay with green start button.

    Displays a green start button in the center of the screen (15% from bottom)
    when frame is detected and automation is not running.
    """

    def __init__(self, main_window):
        super().__init__()
        self.logging = logging.getLogger(self.__class__.__name__)
        self.main_window = main_window

        # Button state tracking
        self._button_visible = False
        self._last_position = None  # Track last position to avoid spam logging

        # Frame detection data cache
        self._frame_detection_data = None  # Cached data to avoid repeated loading

        # Stage frame detection files if needed
        self.stage_frame_detection_files()

        # Setup the overlay window
        self.setup_window()

        # Create the green start button
        self.setup_button()

        # Setup visibility update timer
        self.setup_visibility_timer()

        self.logging.debug("FrameDetector initialized")

    def setup_window(self):
        """Configure the overlay window properties."""
        # Make it a frameless overlay that stays on top
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.Tool  # Prevents it from appearing in taskbar
        )

        # Make background transparent
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

        # Set initial size and position
        self.resize(120, 50)
        self.center_on_frame()

        self.logging.debug("FrameDetector window configured")

    def setup_button(self):
        """Create and configure the green start button."""
        self.start_button = QPushButton("▶ START", self)

        # Style the button as a green start button
        self.start_button.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                border: 2px solid #45a049;
                border-radius: 20px;
                color: white;
                font-weight: bold;
                font-size: 14px;
                padding: 10px 20px;
            }
            QPushButton:hover {
                background-color: #45a049;
                border-color: #3d8b40;
            }
            QPushButton:pressed {
                background-color: #3d8b40;
            }
        """)

        # Set button size and position
        self.start_button.resize(120, 50)
        self.start_button.move(0, 0)

        # Connect button click (placeholder for now)
        self.start_button.clicked.connect(self.on_start_clicked)

        self.logging.debug("FrameDetector button configured")

    def setup_visibility_timer(self):
        """Setup timer to regularly check visibility conditions."""
        self.visibility_timer = QTimer()
        self.visibility_timer.timeout.connect(self.update_visibility)
        self.visibility_timer.start(1000)  # Check every 1 second (reduced from 500ms)

        self.logging.debug("FrameDetector visibility timer started")

    def center_on_frame(self):
        """Position the button in center of frame, 15% from bottom of frame."""
        # Get frame area from cache manager
        if not self.main_window or not hasattr(self.main_window, "window_manager"):
            self.logging.warning("No window manager found, using default position")
            self.move(100, 100)
            return

        frame_area = self.main_window.window_manager.get_frame_area()
        if not frame_area:
            self.logging.warning("No frame area found, using default position")
            self.move(100, 100)
            return

        # Calculate position: center horizontally within frame, 15% from bottom of frame
        frame_x = frame_area["x"]
        frame_y = frame_area["y"]
        frame_width = frame_area["width"]
        frame_height = frame_area["height"]

        # Center horizontally within the frame
        x = frame_x + (frame_width - self.width()) // 2

        # Position 15% from bottom of frame
        y = frame_y + int(frame_height * 0.85 - self.height())

        # Only move and log if position actually changed
        new_position = (x, y)
        if new_position != self._last_position:
            self.move(x, y)
            self._last_position = new_position
            self.logging.debug(f"FrameDetector repositioned to ({x}, {y}) within frame area {frame_area}")
        # If position unchanged, don't move or log (reduces spam)

    def should_be_visible(self):
        """
        Determine if the button should be visible based on application state.

        Visibility Rules:
        - ✅ App running (normal)
        - ✅ App minimized to title bar
        - ❌ App minimized to taskbar
        - ❌ Automation is running
        - ✅ Frame detected (placeholder: always True)
        """
        # Check if main window exists and is accessible
        if not self.main_window:
            return False

        # Check if automation is running (hide button if any automation is active)
        if hasattr(self.main_window, "automation_controller"):
            if hasattr(self.main_window.automation_controller, "active_automators"):
                if self.main_window.automation_controller.active_automators:
                    return False

        # Check if app is minimized to taskbar (hide button)
        if self.main_window.isMinimized():
            return False

        # Check if main window is visible (app running normally or minimized to title bar)
        if not self.main_window.isVisible():
            return False

        # Frame detection placeholder - always return True for now
        frame_detected = self.detect_frame_placeholder()
        if not frame_detected:
            return False

        # All conditions met - button should be visible
        return True

    def detect_frame_placeholder(self):
        """
        Frame detection logic using cached border analysis data.
        Returns True if a frame is detected, False otherwise.
        """
        # Load frame detection data once and cache it
        if self._frame_detection_data is None:
            self._frame_detection_data = self.load_frame_detection_data()
            if self._frame_detection_data is None:
                # No frame detection data available, default to True for now
                return True

        # TODO: Implement actual frame detection logic using cached border analysis data
        # For now, return True since we have the data cached and ready
        # Real implementation would analyze current screen against the cached border patterns
        return True

    def update_visibility(self):
        """Update button visibility and position based on current application state."""
        should_show = self.should_be_visible()

        if should_show and not self._button_visible:
            self.center_on_frame()  # Update position when showing
            self.show()
            self._button_visible = True
            self.logging.debug("FrameDetector button shown")
        elif not should_show and self._button_visible:
            self.hide()
            self._button_visible = False
            self.logging.debug("FrameDetector button hidden")
        elif should_show and self._button_visible:
            # Button is visible, update position in case frame moved
            self.center_on_frame()

    def on_start_clicked(self):
        """Handle start button click (placeholder)."""
        self.logging.info("FrameDetector start button clicked")
        # TODO: Implement frame detection start logic

    def cleanup(self):
        """Clean up resources when application closes."""
        if hasattr(self, "visibility_timer"):
            self.visibility_timer.stop()

        # Clear cached data
        self._frame_detection_data = None

        self.hide()
        self.logging.debug("FrameDetector cleaned up")

    def stage_frame_detection_files(self):
        """
        Stage frame detection files by copying latest border analysis to frame_detection files.

        If frame_detection.json or frame_detection.pkl don't exist in config/data/,
        copy the latest border_analysis file from config/analysis/ to config/data/frame_detection.json
        and create a pickle version at config/data/frame_detection.pkl
        """
        # Define paths
        config_dir = Path(__file__).parent.parent.parent / "config"
        data_dir = config_dir / "data"
        analysis_dir = config_dir / "analysis"

        frame_detection_json = data_dir / "frame_detection.json"
        frame_detection_pkl = data_dir / "frame_detection.pkl"

        # Check if either file already exists
        if frame_detection_json.exists() or frame_detection_pkl.exists():
            self.logging.debug("Frame detection files already exist, skipping staging")
            return

        # Find latest border analysis file
        try:
            border_files = list(analysis_dir.glob("border_analysis_*.json"))
            if not border_files:
                self.logging.warning("No border analysis files found in config/analysis/")
                return

            # Sort by filename (which includes timestamp) to get latest
            latest_border_file = sorted(border_files)[-1]
            self.logging.debug(f"Found latest border analysis: {latest_border_file.name}")

            # Load the border analysis data
            with open(latest_border_file, "r", encoding="utf-8") as f:
                border_data = json.load(f)

            # Create data directory if it doesn't exist
            data_dir.mkdir(parents=True, exist_ok=True)

            # Copy to frame_detection.json
            with open(frame_detection_json, "w", encoding="utf-8") as f:
                json.dump(border_data, f, indent=2)

            # Create pickle version for faster loading
            with open(frame_detection_pkl, "wb") as f:
                pickle.dump(border_data, f)

            self.logging.info(f"Staged frame detection files from {latest_border_file.name}")
            self.logging.debug(f"Created: {frame_detection_json}")
            self.logging.debug(f"Created: {frame_detection_pkl}")

        except Exception as e:
            self.logging.error(f"Failed to stage frame detection files: {e}")

    def load_frame_detection_data(self):
        """
        Load frame detection data from staged files.
        Prefers pickle file for speed, falls back to JSON.
        This method should only be called once and the result cached.
        """
        config_dir = Path(__file__).parent.parent.parent / "config"
        data_dir = config_dir / "data"

        frame_detection_pkl = data_dir / "frame_detection.pkl"
        frame_detection_json = data_dir / "frame_detection.json"

        try:
            # Try pickle first (faster)
            if frame_detection_pkl.exists():
                with open(frame_detection_pkl, "rb") as f:
                    data = pickle.load(f)
                    self.logging.debug("Loaded frame detection data from pickle file (cached for reuse)")
                    return data

            # Fall back to JSON
            elif frame_detection_json.exists():
                with open(frame_detection_json, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self.logging.debug("Loaded frame detection data from JSON file (cached for reuse)")
                    return data

            else:
                self.logging.warning("No frame detection data files found")
                return None

        except Exception as e:
            self.logging.error(f"Failed to load frame detection data: {e}")
            return None
