#!/usr/bin/env python3
"""
Minigame Detection System for Widget Automation Tool
"""

import cv2
import numpy as np
import pytesseract
import json
import time
from typing import Dict, List, Optional, Tuple
from widget_inc_manager import WidgetIncManager


class MinigameDetector:
    def __init__(self, widget_manager=None):
        self.widget_manager = widget_manager or WidgetIncManager()
        self.detection_patterns = self.load_detection_patterns()
        self.last_detection_time = 0
        self.detection_cache = {}
        self.debug_mode = False
        self.enable_logging = False

    def load_detection_patterns(self) -> List[Dict]:
        """Load detection patterns from minigames.json"""
        try:
            with open("config/minigames.json", "r") as f:
                config = json.load(f)
                return config.get("detection_patterns", [])
        except Exception as e:
            print(f"Error loading detection patterns: {e}")
            return []

    def capture_window_screenshot(self) -> Optional[np.ndarray]:
        """Capture screenshot of WidgetInc window"""
        try:
            import pyautogui

            if not self.widget_manager.find_widget_inc_window():
                return None

            window = self.widget_manager.window
            if not window:
                return None

            # Capture the window
            screenshot = pyautogui.screenshot(
                region=(window.left, window.top, window.width, window.height)
            )

            # Convert to OpenCV format
            return cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2BGR)

        except Exception as e:
            if self.enable_logging:
                print(f"Error capturing screenshot: {e}")
            return None

    def extract_text_from_image(self, image: np.ndarray) -> List[str]:
        """Extract text from image using OCR"""
        try:
            # Convert to grayscale for better OCR
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

            # Apply some preprocessing for better text recognition
            # Increase contrast
            alpha = 1.5  # Contrast control
            beta = 30  # Brightness control
            enhanced = cv2.convertScaleAbs(gray, alpha=alpha, beta=beta)

            # Apply threshold
            _, thresh = cv2.threshold(
                enhanced, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU
            )

            # Extract text
            text = pytesseract.image_to_string(thresh, config="--psm 6")

            # Split into lines and clean up
            lines = [line.strip() for line in text.split("\n") if line.strip()]

            if self.enable_logging:
                print(f"Extracted text: {lines}")

            return lines

        except Exception as e:
            if self.enable_logging:
                print(f"Error extracting text: {e}")
            return []

    def detect_current_minigame(self) -> Optional[Dict]:
        """Detect current minigame based on text identifiers"""
        try:
            # Rate limiting - don't check too frequently
            current_time = time.time()
            if current_time - self.last_detection_time < 0.5:  # Check every 0.5 seconds
                return self.detection_cache.get("last_result")

            self.last_detection_time = current_time

            # Capture screenshot
            screenshot = self.capture_window_screenshot()
            if screenshot is None:
                return None

            # Extract text
            extracted_text = self.extract_text_from_image(screenshot)
            if not extracted_text:
                return None

            # Check against detection patterns
            for pattern in self.detection_patterns:
                text_identifiers = pattern.get("text_identifiers", [])
                matches_found = 0

                for identifier in text_identifiers:
                    for extracted in extracted_text:
                        if identifier.lower() in extracted.lower():
                            matches_found += 1
                            break

                # If we found matches for this pattern
                if matches_found > 0:
                    result = {
                        "name": pattern["name"],
                        "has_logic": pattern.get("has_logic", False),
                        "matches_found": matches_found,
                        "total_identifiers": len(text_identifiers),
                        "confidence": matches_found / len(text_identifiers),
                        "matched_text": extracted_text,
                    }

                    # Cache the result
                    self.detection_cache["last_result"] = result

                    if self.enable_logging:
                        print(
                            f"Detected minigame: {result['name']} (confidence: {result['confidence']:.2f})"
                        )

                    return result

            # No matches found
            self.detection_cache["last_result"] = None
            return None

        except Exception as e:
            if self.enable_logging:
                print(f"Error in detect_current_minigame: {e}")
            return None

    def set_debug_mode(self, enabled: bool):
        """Enable/disable debug mode"""
        self.debug_mode = enabled

    def set_logging(self, enabled: bool):
        """Enable/disable logging"""
        self.enable_logging = enabled
