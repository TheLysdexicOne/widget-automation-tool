"""
Text Detection Module - Core text detection using glyph matching.

This module handles all text detection operations using glyph-based matching.
Following separation of duties: Core (brains) performs text detection operations.
"""

import logging
import os
import json
import time
from typing import Dict, List, Optional, Tuple, Any
from pathlib import Path

try:
    from PIL import Image, ImageDraw, ImageFont
    import cv2
    import numpy as np

    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False
    logging.warning("PIL or OpenCV not available - text detection will be disabled")

from PyQt6.QtCore import QObject, pyqtSignal


class TextDetector(QObject):
    """Handles text detection using glyph matching."""

    # Signals for notifying other components
    text_detected = pyqtSignal(dict)  # Emits detected text info
    zone_scanned = pyqtSignal(str, list)  # Emits zone name and found text

    def __init__(self, config_path: str = "config/text_detection.json"):
        super().__init__()
        self.logger = logging.getLogger(__name__)

        # Load configuration
        self.config = self._load_config(config_path)
        self.glyphs = {}
        self.glyph_cache = {}

        # Initialize if PIL is available
        if PIL_AVAILABLE:
            self._initialize_glyphs()
        else:
            self.logger.error("PIL/OpenCV not available - text detection disabled")

    def _load_config(self, config_path: str) -> Dict[str, Any]:
        """Load text detection configuration from JSON file."""
        try:
            with open(config_path, "r") as f:
                config = json.load(f)
                self.logger.info(f"Text detection config loaded from {config_path}")
                return config
        except Exception as e:
            self.logger.error(f"Failed to load config from {config_path}: {e}")
            return self._get_default_config()

    def _get_default_config(self) -> Dict[str, Any]:
        """Return default configuration if config file fails to load."""
        return {
            "font_settings": {
                "font_path": "assets/font/pixelFJ8pt1_.ttf",
                "font_size": 8,
                "font_color": "#ffffff",
                "border_color": "#131422",
                "base_resolution": {"width": 2160, "height": 1440},
            },
            "glyph_settings": {
                "characters": "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789!@#$%^&*()_+-=[]{}|;':\",.<>?/ ",
                "match_threshold": 0.95,
                "spacing_tolerance": 2,
                "output_directory": "assets/glyphs/",
                "cache_enabled": True,
            },
            "detection_zones": {},
        }

    def _initialize_glyphs(self):
        """Initialize glyph atlas for text matching."""
        if not PIL_AVAILABLE:
            return

        try:
            font_settings = self.config["font_settings"]
            glyph_settings = self.config["glyph_settings"]

            # Create glyphs directory if it doesn't exist
            glyph_dir = Path(glyph_settings["output_directory"])
            glyph_dir.mkdir(parents=True, exist_ok=True)

            # Check if glyphs need to be regenerated
            if self._should_regenerate_glyphs():
                self._generate_glyph_atlas()

            # Load existing glyphs
            self._load_glyph_atlas()

            self.logger.info(
                f"Text detection initialized with {len(self.glyphs)} glyphs"
            )

        except Exception as e:
            self.logger.error(f"Failed to initialize glyphs: {e}")

    def _should_regenerate_glyphs(self) -> bool:
        """Check if glyphs need to be regenerated."""
        glyph_settings = self.config["glyph_settings"]
        glyph_dir = Path(glyph_settings["output_directory"])

        # Check if glyph directory exists and has files
        if not glyph_dir.exists() or not list(glyph_dir.glob("*.png")):
            return True

        # Check if font file is newer than glyphs
        font_path = Path(self.config["font_settings"]["font_path"])
        if font_path.exists():
            font_time = font_path.stat().st_mtime
            glyph_files = list(glyph_dir.glob("*.png"))
            if glyph_files:
                glyph_time = min(f.stat().st_mtime for f in glyph_files)
                return font_time > glyph_time

        return False

    def _generate_glyph_atlas(self):
        """Generate glyph atlas from font."""
        try:
            font_settings = self.config["font_settings"]
            glyph_settings = self.config["glyph_settings"]

            # Load font
            font_path = font_settings["font_path"]
            font_size = font_settings["font_size"]

            if not os.path.exists(font_path):
                self.logger.error(f"Font file not found: {font_path}")
                return

            font = ImageFont.truetype(font_path, font_size)

            # Colors
            font_color = self._hex_to_rgb(font_settings["font_color"])
            border_color = self._hex_to_rgb(font_settings["border_color"])

            # Output directory
            output_dir = Path(glyph_settings["output_directory"])
            output_dir.mkdir(parents=True, exist_ok=True)

            # Generate glyphs for each character
            characters = glyph_settings["characters"]
            self.logger.info(f"Generating {len(characters)} glyphs...")

            for char in characters:
                try:
                    glyph_img = self._render_character(
                        char, font, font_color, border_color
                    )
                    if glyph_img:
                        # Save with character code and character for easy identification
                        safe_char = char if char.isalnum() else f"_{ord(char)}_"
                        filename = f"{ord(char)}_{safe_char}.png"
                        filepath = output_dir / filename
                        glyph_img.save(filepath)

                except Exception as e:
                    self.logger.warning(f"Failed to generate glyph for '{char}': {e}")

            self.logger.info("Glyph atlas generated successfully")

        except Exception as e:
            self.logger.error(f"Failed to generate glyph atlas: {e}")

    def _render_character(
        self,
        char: str,
        font,
        font_color: Tuple[int, int, int],
        border_color: Tuple[int, int, int],
    ) -> Optional[Image.Image]:
        """Render a single character with font and border."""
        try:
            # Get text size
            bbox = font.getbbox(char)
            width = bbox[2] - bbox[0]
            height = bbox[3] - bbox[1]

            # Create image with padding for border
            padding = 2
            img_width = width + padding * 2
            img_height = height + padding * 2

            img = Image.new("RGBA", (img_width, img_height), (0, 0, 0, 0))
            draw = ImageDraw.Draw(img)

            # Draw border (outline)
            base_x = padding - bbox[0]
            base_y = padding - bbox[1]

            for dx in [-1, 0, 1]:
                for dy in [-1, 0, 1]:
                    if dx != 0 or dy != 0:  # Don't draw on center
                        draw.text(
                            (base_x + dx, base_y + dy),
                            char,
                            font=font,
                            fill=border_color + (255,),
                        )

            # Draw main text
            draw.text((base_x, base_y), char, font=font, fill=font_color + (255,))

            return img

        except Exception as e:
            self.logger.warning(f"Failed to render character '{char}': {e}")
            return None

    def _load_glyph_atlas(self):
        """Load generated glyph atlas into memory."""
        try:
            glyph_settings = self.config["glyph_settings"]
            glyph_dir = Path(glyph_settings["output_directory"])

            self.glyphs = {}

            for glyph_file in glyph_dir.glob("*.png"):
                try:
                    # Extract character code from filename
                    parts = glyph_file.stem.split("_", 1)
                    char_code = int(parts[0])
                    char = chr(char_code)

                    # Load and convert to grayscale for matching
                    img = Image.open(glyph_file).convert("L")
                    self.glyphs[char] = np.array(img)

                except Exception as e:
                    self.logger.warning(f"Failed to load glyph {glyph_file}: {e}")

            self.logger.info(f"Loaded {len(self.glyphs)} glyphs into atlas")

        except Exception as e:
            self.logger.error(f"Failed to load glyph atlas: {e}")

    def _hex_to_rgb(self, hex_color: str) -> Tuple[int, int, int]:
        """Convert hex color to RGB tuple."""
        hex_color = hex_color.lstrip("#")
        return tuple(int(hex_color[i : i + 2], 16) for i in (0, 2, 4))

    def detect_text_in_region(
        self, image: Image.Image, region: Dict[str, float]
    ) -> List[str]:
        """Detect text in a specific region of an image."""
        if not PIL_AVAILABLE or not self.glyphs:
            return []

        try:
            # Calculate absolute coordinates from percentages
            img_width, img_height = image.size
            x = int(region["x_percent"] * img_width)
            y = int(region["y_percent"] * img_height)
            width = int(region["width_percent"] * img_width)
            height = int(region["height_percent"] * img_height)

            # Crop region
            region_img = image.crop((x, y, x + width, y + height))

            # Convert to grayscale for matching
            gray_img = np.array(region_img.convert("L"))

            # Perform glyph matching
            detected_text = self._match_glyphs_in_image(gray_img)

            return detected_text

        except Exception as e:
            self.logger.error(f"Failed to detect text in region: {e}")
            return []

    def _match_glyphs_in_image(self, image: np.ndarray) -> List[str]:
        """Match glyphs in an image using template matching."""
        try:
            glyph_settings = self.config["glyph_settings"]
            threshold = glyph_settings["match_threshold"]

            found_text = []

            # Try to match each line of text
            # For now, we'll do a simple horizontal scan
            height, width = image.shape

            # Look for text lines by finding horizontal regions with bright pixels
            line_height = 16  # Approximate character height
            for y in range(0, height - line_height, line_height // 2):
                line_img = image[y : y + line_height, :]
                line_text = self._match_glyphs_in_line(line_img, threshold)
                if line_text.strip():
                    found_text.append(line_text.strip())

            return found_text

        except Exception as e:
            self.logger.error(f"Failed to match glyphs: {e}")
            return []

    def _match_glyphs_in_line(self, line_image: np.ndarray, threshold: float) -> str:
        """Match glyphs in a single line of text."""
        try:
            text = ""
            x = 0
            line_height, line_width = line_image.shape

            while x < line_width:
                best_match = None
                best_score = 0
                best_width = 0

                # Try to match each glyph at current position
                for char, glyph in self.glyphs.items():
                    glyph_height, glyph_width = glyph.shape

                    # Skip if glyph doesn't fit
                    if x + glyph_width > line_width or glyph_height > line_height:
                        continue

                    # Extract region for comparison
                    region = line_image[0:glyph_height, x : x + glyph_width]

                    # Template matching
                    result = cv2.matchTemplate(region, glyph, cv2.TM_CCOEFF_NORMED)
                    _, max_val, _, _ = cv2.minMaxLoc(result)

                    # Check if this is the best match
                    if max_val > best_score and max_val >= threshold:
                        best_match = char
                        best_score = max_val
                        best_width = glyph_width

                # Add matched character or advance
                if best_match:
                    text += best_match
                    x += best_width
                else:
                    x += 1  # Advance by one pixel if no match

            return text

        except Exception as e:
            self.logger.error(f"Failed to match glyphs in line: {e}")
            return ""

    def scan_zones(
        self, image: Image.Image, zones: List[str] = None
    ) -> Dict[str, List[str]]:
        """Scan specific zones for text detection."""
        if not PIL_AVAILABLE or not self.glyphs:
            return {}

        try:
            detection_zones = self.config["detection_zones"]
            zones_to_scan = zones if zones else list(detection_zones.keys())

            results = {}

            for zone_name in zones_to_scan:
                if zone_name not in detection_zones:
                    continue

                zone_config = detection_zones[zone_name]
                region = zone_config["region"]

                # Detect text in this zone
                detected_text = self.detect_text_in_region(image, region)
                results[zone_name] = detected_text

                # Emit signal for this zone
                self.zone_scanned.emit(zone_name, detected_text)

                if detected_text:
                    self.logger.debug(f"Zone '{zone_name}' detected: {detected_text}")

            # Emit overall results
            self.text_detected.emit(results)

            return results

        except Exception as e:
            self.logger.error(f"Failed to scan zones: {e}")
            return {}

    def get_zone_info(self, zone_name: str) -> Optional[Dict[str, Any]]:
        """Get configuration info for a specific zone."""
        detection_zones = self.config["detection_zones"]
        return detection_zones.get(zone_name)

    def get_available_zones(self) -> List[str]:
        """Get list of available detection zones."""
        return list(self.config["detection_zones"].keys())

    def is_available(self) -> bool:
        """Check if text detection is available."""
        return PIL_AVAILABLE and bool(self.glyphs)
