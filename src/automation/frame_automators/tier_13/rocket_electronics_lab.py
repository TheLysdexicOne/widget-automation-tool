"""
Rocket Electronics Lab Automator (Frame ID: 13.1)
Handles automation for the Rocket Electronics Lab frame in WidgetInc.
"""

import time
import easyocr
import numpy as np

from PIL import Image, ImageFilter, ImageGrab
from typing import Any, Dict
from automation.base_automator import BaseAutomator


class RocketElectronicsLabAutomator(BaseAutomator):
    """Automation logic for Rocket Electronics Lab (Frame 13.1)."""

    def __init__(self, frame_data: Dict[str, Any]):
        super().__init__(frame_data)
        # Initialize OCR reader for binary (0/1) only
        self.ocr_reader = easyocr.Reader(["en"])
        self.allowed_chars = "01"

    def preprocess_binary_image(self, image):
        """Extract white pixels and create clean image for OCR."""
        img_processed = Image.new("RGB", image.size, (0, 0, 0))
        for x in range(image.width):
            for y in range(image.height):
                pixel = image.getpixel((x, y))
                if pixel == (255, 255, 255):
                    img_processed.putpixel((x, y), (255, 255, 255))
        return img_processed

    def read_binary(self, reading_bbox):
        """Read binary sequence from screen area."""
        # Capture area
        reading_image = ImageGrab.grab(bbox=reading_bbox, all_screens=True)
        # Preprocess for OCR
        # Convert to grayscale and blur for better OCR
        img_test = reading_image.convert("L")
        img_test = img_test.filter(ImageFilter.GaussianBlur(radius=0.8))
        # Run OCR
        results = self.ocr_reader.readtext(np.array(img_test), allowlist=self.allowed_chars)
        if results:
            # EasyOCR returns [(bbox, text, confidence), ...]
            bbox, text, confidence = results[0]
            return str(text), float(confidence)
        return "", 0.0

    def run_automation(self):
        start_time = time.time()

        reading_bbox = self.frame_data["bbox"]["reading_bbox"]
        zero = self.frame_data["interactions"]["0"]
        one = self.frame_data["interactions"]["1"]

        # Main automation loop
        while self.should_continue:
            if time.time() - start_time > self.max_run_time:
                break

            binary_text, confidence = self.read_binary(reading_bbox)
            self.logger.info(f"Read binary: {binary_text} (confidence: {confidence})")

            # Click each bit in order using zero and one interaction points
            for bit in binary_text:
                if not self.should_continue:
                    break
                if bit == "0":
                    self.click(*zero)
                elif bit == "1":
                    self.click(*one)
                self.sleep(0.1)

            if not self.sleep(1):
                break
