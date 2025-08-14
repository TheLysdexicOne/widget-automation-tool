import logging
import json
import pickle
import os
import time
import numpy as np
from pathlib import Path
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtWidgets import QWidget, QPushButton, QLabel

from utility.logging_utils import LoggerMixin
from utility.window_utils import get_frame_screenshot
from utility.coordinate_utils import conv_frame_percent_to_screen_coords


class HoverButton(QPushButton):
    """Custom QPushButton that emits hover events to parent."""

    def __init__(self, text, parent=None):
        super().__init__(text, parent)
        self.parent_detector = parent

    def enterEvent(self, event):
        """Mouse entered button area."""
        super().enterEvent(event)
        if self.parent_detector and hasattr(self.parent_detector, "on_button_hover_enter"):
            self.parent_detector.on_button_hover_enter(event)

    def leaveEvent(self, event):
        """Mouse left button area."""
        super().leaveEvent(event)
        if self.parent_detector and hasattr(self.parent_detector, "on_button_hover_leave"):
            self.parent_detector.on_button_hover_leave(event)


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
        self._current_frame_info = None  # Cache current frame detection result
        self._last_detection_time = 0  # Timestamp of last detection

        # Logging throttling to prevent spam
        self._last_log_message = None
        self._last_log_time = 0

        # State change tracking for logging
        self._last_detected_frame_id = None
        self._last_detection_method = None

        # Stage frame detection files if needed
        self.stage_frame_detection_files()

        # Setup the overlay window
        self.setup_window()

        # Create the green start button
        self.setup_button()

        # Setup visibility update timer
        self.setup_visibility_timer()

        self.logging.debug("FrameDetector initialized")

    def _log_throttled(self, level, message, throttle_seconds=10):
        """Log a message with throttling to prevent spam."""
        import time

        current_time = time.time()

        # Check if this is the same message as last time and within throttle window
        if self._last_log_message == message and current_time - self._last_log_time < throttle_seconds:
            return  # Skip logging - too soon for same message

        # Log the message
        getattr(self.logging, level)(message)
        self._last_log_message = message
        self._last_log_time = current_time

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

        # Set initial size and position (increased height for label)
        self.resize(150, 80)  # Increased width from 120 to 150 to fit longer label
        self.center_on_frame()

        self.logging.debug("FrameDetector window configured")

    def setup_button(self):
        """Create and configure the green start button."""
        self.start_button = HoverButton("▶ START", self)

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

        # Connect button click
        self.start_button.clicked.connect(self.on_start_clicked)

        # Create frame info label (initially hidden)
        self.frame_info_label = QLabel(self)
        self.frame_info_label.setStyleSheet("""
            QLabel {
                background-color: rgba(0, 0, 0, 180);
                color: white;
                border: 1px solid #555;
                border-radius: 5px;
                padding: 4px 8px;
                font-size: 11px;
                font-weight: normal;
            }
        """)
        self.frame_info_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.frame_info_label.hide()

        # Position label below the button
        self.frame_info_label.move(0, 55)  # Just below the 50px tall button
        self.frame_info_label.resize(150, 20)  # Increased width from 120 to 150 for longer text

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

        # Frame detection - implement actual detection logic
        frame_detected, detected_frame = self.detect_current_frame()
        if not frame_detected:
            return False

        # Check confidence threshold - reject low confidence detections
        if detected_frame and detected_frame.get("confidence", 0) <= 0.95:
            # Log confidence rejection as state change (only once)
            if self._last_detected_frame_id is not None:
                frame_name = detected_frame.get("frame_name", "Unknown")
                confidence = detected_frame.get("confidence", 0)
                self.logging.debug(
                    f"Frame rejected due to low confidence: {frame_name} (Confidence: {confidence:.2f} ≤ 0.95)"
                )
                self._last_detected_frame_id = None
                self._last_detection_method = None
            return False

        # All conditions met - button should be visible
        return True

    def detect_current_frame(self):
        """
        Detect the current frame using border analysis data.
        Returns (detected: bool, frame_info: dict or None)
        """
        # Cache detection results for 2 seconds to avoid repeated analysis
        current_time = time.time()
        if self._current_frame_info is not None and current_time - self._last_detection_time < 2.0:
            return True, self._current_frame_info

        # Load frame detection data once and cache it
        if self._frame_detection_data is None:
            self._frame_detection_data = self.load_frame_detection_data()
            if self._frame_detection_data is None:
                # No frame detection data available, default to detected=True, frame=None
                return True, None

        # Get current frame area for screenshot analysis
        if not self.main_window or not hasattr(self.main_window, "window_manager"):
            return False, None

        frame_area = self.main_window.window_manager.get_frame_area()
        if not frame_area:
            return False, None

        try:
            # Primary detection: Analyze borders using cached frame detection data
            detected_frame = self.analyze_frame_borders(frame_area)

            # Secondary detection for identical frames (Gyroscope Fabricator vs Widget Spinner)
            if detected_frame and self.needs_secondary_detection(detected_frame):
                secondary_result = self.secondary_frame_detection(detected_frame, frame_area)
                detected_frame = secondary_result

            # Log only on state changes (frame ID or detection method change)
            if detected_frame:
                current_frame_id = detected_frame.get("frame_id")
                current_method = detected_frame.get("detection_method")

                # Check if this is a state change worth logging
                if current_frame_id != self._last_detected_frame_id or current_method != self._last_detection_method:
                    self.logging.debug(
                        f"Frame detected: {detected_frame.get('frame_name', 'Unknown')} "
                        f"(ID: {current_frame_id}, "
                        f"Confidence: {detected_frame.get('confidence', 0):.2f}, "
                        f"Method: {current_method})"
                    )

                    # Update state tracking
                    self._last_detected_frame_id = current_frame_id
                    self._last_detection_method = current_method
            else:
                # Log frame loss only once
                if self._last_detected_frame_id is not None:
                    self.logging.debug("Frame detection lost")
                    self._last_detected_frame_id = None
                    self._last_detection_method = None

            # Cache the result
            self._current_frame_info = detected_frame
            self._last_detection_time = current_time

            if detected_frame:
                return True, detected_frame
            else:
                return False, None

        except Exception as e:
            self.logging.error(f"Frame detection failed: {e}")
            return False, None

    def analyze_frame_borders(self, frame_area):
        """
        Analyze frame borders against cached border analysis data.
        Uses the same percentage-based methodology as the analyze package.
        Returns the detected frame info or None.
        """
        if not self._frame_detection_data:
            return None

        try:
            # Capture current frame screenshot
            screenshot = get_frame_screenshot()
            if screenshot is None:
                self.logging.warning("Could not capture frame screenshot for border analysis")
                return None

            # Convert to numpy array for processing (same as analyze package)
            img_array = np.array(screenshot)
            height, width = img_array.shape[:2]

            # Use same parameters as analyze package
            border_inset = 0.05  # 5% inset from edge
            center_strip = 0.2  # 20% center strip

            # Extract left border using analyze package methodology
            inset_width = int(width * border_inset)
            strip_height = int(height * center_strip)

            center_y = height // 2
            start_y = center_y - strip_height // 2
            end_y = start_y + strip_height

            # Extract border regions (exact same method as analyze package)
            left_border = img_array[start_y:end_y, 0:inset_width]
            right_border_start_x = width - inset_width
            right_border = img_array[start_y:end_y, right_border_start_x:width]

            # Calculate average colors for left and right borders
            left_avg_color = np.mean(left_border, axis=(0, 1))[:3]  # RGB only
            right_avg_color = np.mean(right_border, axis=(0, 1))[:3]  # RGB only

            # Find best matching frame using color similarity
            best_match = None
            best_score = float("inf")  # Lower score = better match

            for frame_key, frame_data in self._frame_detection_data.items():
                if "left_border" not in frame_data or "right_border" not in frame_data:
                    continue

                # Get stored border colors
                stored_left_color = frame_data["left_border"]["average_color"]
                stored_right_color = frame_data["right_border"]["average_color"]

                # Calculate color distance (Euclidean distance in RGB space)
                left_distance = np.sqrt(np.sum((left_avg_color - stored_left_color) ** 2))
                right_distance = np.sqrt(np.sum((right_avg_color - stored_right_color) ** 2))

                # Combined score (both borders must match reasonably well)
                combined_score = left_distance + right_distance

                # Threshold for acceptable match (adjust based on testing)
                if combined_score < 100 and combined_score < best_score:  # Reasonable threshold
                    best_score = combined_score
                    best_match = frame_data

            if best_match:
                confidence = max(0.0, min(1.0, 1.0 - (best_score / 200)))  # Convert score to confidence
                return {
                    "frame_id": best_match["frame_id"],
                    "frame_name": best_match["frame_name"],
                    "confidence": confidence,
                    "detection_method": "border_analysis",
                }
            else:
                self._log_throttled("debug", "No suitable border match found", throttle_seconds=10)
                return None

        except Exception as e:
            self.logging.error(f"Border analysis failed: {e}")
            return None

    def needs_secondary_detection(self, detected_frame):
        """
        Check if frame needs secondary detection due to similarity conflicts.
        Returns True if secondary detection is needed.
        """
        if not detected_frame:
            return False

        frame_name = detected_frame.get("frame_name", "")

        # Frames that need secondary detection (from similarity analysis)
        conflicting_frames = ["Gyroscope Fabricator", "Widget Spinner"]

        return frame_name in conflicting_frames

    def secondary_frame_detection(self, primary_detection, frame_area):
        """
        Secondary detection for frames with identical borders.
        Uses red button analysis to disambiguate between Gyroscope Fabricator and Widget Spinner.
        """
        frame_name = primary_detection.get("frame_name", "")

        # Handle Gyroscope Fabricator vs Widget Spinner conflict
        if frame_name in ["Gyroscope Fabricator", "Widget Spinner"]:
            disambiguated_frame = self.disambiguate_gyroscope_vs_spinner(frame_area)
            if disambiguated_frame:
                # Update both frame_name AND frame_id to match the correct frame
                correct_frame_id = "2.3" if disambiguated_frame == "Gyroscope Fabricator" else "2.4"

                return {
                    **primary_detection,
                    "frame_id": correct_frame_id,  # Fix: Update frame_id to match frame_name
                    "frame_name": disambiguated_frame,
                    "detection_method": "secondary_red_button",
                    "confidence": 0.98,  # Higher confidence from secondary detection
                }

        return primary_detection

    def disambiguate_gyroscope_vs_spinner(self, frame_area):
        """
        Disambiguate between Gyroscope Fabricator and Widget Spinner using red button analysis.
        Returns the correct frame name or None.
        """
        try:
            # Capture current frame screenshot
            screenshot = get_frame_screenshot()
            if screenshot is None:
                self.logging.warning("Could not capture frame screenshot for button analysis")
                return "Gyroscope Fabricator"  # Default fallback

            # Define button positions (frame percentages converted to pixel coordinates)
            # Gyroscope Fabricator: "create" button at [0.5312, 0.5661]
            # Widget Spinner: "spin" button at [0.68305, 0.601352]

            frame_width = screenshot.width
            frame_height = screenshot.height

            # Convert frame percentage coordinates to pixel coordinates
            gyro_button_x = int(0.5312 * frame_width)
            gyro_button_y = int(0.5661 * frame_height)

            spinner_button_x = int(0.68305 * frame_width)
            spinner_button_y = int(0.601352 * frame_height)

            # Sample colors at button positions
            gyro_button_color = screenshot.getpixel((gyro_button_x, gyro_button_y))
            spinner_button_color = screenshot.getpixel((spinner_button_x, spinner_button_y))

            # Define red button color ranges (from automation system)
            red_colors = {"default": (199, 35, 21), "focus": (251, 36, 18), "inactive": (57, 23, 20)}

            def is_red_button(color_tuple):
                """Check if a color matches any red button state."""
                r, g, b = color_tuple[:3]  # Handle both RGB and RGBA
                tolerance = 15  # Slightly higher tolerance for detection

                for state_color in red_colors.values():
                    if all(
                        abs(r - state_color[0]) <= tolerance
                        and abs(g - state_color[1]) <= tolerance
                        and abs(b - state_color[2]) <= tolerance
                        for _ in [1]
                    ):
                        return True
                return False

            # Check which button position has a red button
            gyro_has_red = is_red_button(gyro_button_color)
            spinner_has_red = is_red_button(spinner_button_color)

            # Throttled logging for button analysis
            if gyro_has_red or spinner_has_red:
                button_analysis_msg = (
                    f"Button analysis - Gyro position {gyro_button_color}: {gyro_has_red}, "
                    f"Spinner position {spinner_button_color}: {spinner_has_red}"
                )
                self._log_throttled("debug", button_analysis_msg, throttle_seconds=10)

            # Determine frame based on button presence
            result = None
            if gyro_has_red and not spinner_has_red:
                result = "Gyroscope Fabricator"
            elif spinner_has_red and not gyro_has_red:
                result = "Widget Spinner"
            elif gyro_has_red and spinner_has_red:
                # Both positions have red - this shouldn't happen, but prioritize Gyroscope
                self.logging.warning("Both button positions show red - defaulting to Gyroscope Fabricator")
                result = "Gyroscope Fabricator"
            else:
                # No red buttons found - might be wrong frame or inactive state
                self._log_throttled(
                    "warning",
                    "No red buttons found at expected positions - defaulting to Gyroscope Fabricator",
                    throttle_seconds=30,
                )
                result = "Gyroscope Fabricator"

            return result

        except Exception as e:
            self.logging.error(f"Button detection failed: {e}")
            return "Gyroscope Fabricator"  # Default fallback

    def get_frame_item_from_cache(self, frame_id):
        """
        Get the item produced by a frame from the frame cache.
        Returns the item name or "Unknown" if not found.
        """
        try:
            if not self.main_window or not hasattr(self.main_window, "window_manager"):
                return "Unknown"

            frame_data = self.main_window.window_manager.get_frame_data(frame_id)
            if frame_data:
                return frame_data.get("item", "Unknown")
            else:
                self.logging.warning(f"Frame data not found for ID: {frame_id}")
                return "Unknown"

        except Exception as e:
            self.logging.error(f"Error getting frame item for {frame_id}: {e}")
            return "Unknown"

    def detect_frame_placeholder(self):
        """
        Legacy placeholder method - replaced by detect_current_frame().
        Kept for backward compatibility during transition.
        """
        detected, frame_info = self.detect_current_frame()
        return detected

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
        """Handle start button click - demonstrate frame detection."""
        self.logging.info("FrameDetector start button clicked")

        # Perform frame detection and report results
        detected, frame_info = self.detect_current_frame()

        if detected and frame_info:
            self.logging.info(
                f"Frame detected: {frame_info['frame_name']} "
                f"(ID: {frame_info['frame_id']}, "
                f"Confidence: {frame_info['confidence']:.2f}, "
                f"Method: {frame_info['detection_method']})"
            )
        elif detected:
            self.logging.info("Frame area detected but no specific frame identified")
        else:
            self.logging.info("No frame detected")

        # TODO: Implement actual automation start logic based on detected frame

    def on_button_hover_enter(self, event):
        """Handle mouse entering the start button - show frame info."""
        # Get current frame detection info
        detected, frame_info = self.detect_current_frame()

        if detected and frame_info:
            frame_id = frame_info.get("frame_id", "N/A")

            # Get item information from frame cache
            item = self.get_frame_item_from_cache(frame_id)

            # Format as "{id}: {item}"
            info_text = f"{frame_id}: {item}"
        else:
            info_text = "No Frame Detected"

        # Set the tooltip text and resize label to fit content
        self.frame_info_label.setText(info_text)
        self.frame_info_label.adjustSize()

        # Center tooltip relative to button center without resizing widget
        # Button is at (0, 0) with width 120px, so center is at x=60
        button_center_x = 60  # self.start_button.width() // 2
        tooltip_width = self.frame_info_label.width()
        tooltip_x = button_center_x - (tooltip_width // 2)

        # Allow tooltip to extend beyond widget bounds if needed (no clamping)
        # This prevents widget from needing to resize and eliminates repositioning

        # Position tooltip below button
        self.frame_info_label.move(tooltip_x, 55)
        self.frame_info_label.show()

    def on_button_hover_leave(self, event):
        """Handle mouse leaving the start button - hide frame info."""
        self.frame_info_label.hide()
        # No widget resizing needed - keeps widget stable and eliminates repositioning

    def cleanup(self):
        """Clean up resources when application closes."""
        if hasattr(self, "visibility_timer"):
            self.visibility_timer.stop()

        # Clear cached data
        self._frame_detection_data = None
        self._current_frame_info = None
        self._last_detection_time = 0

        # Clear state tracking
        self._last_detected_frame_id = None
        self._last_detection_method = None

        # Hide and clean up UI elements
        if hasattr(self, "frame_info_label"):
            self.frame_info_label.hide()

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
