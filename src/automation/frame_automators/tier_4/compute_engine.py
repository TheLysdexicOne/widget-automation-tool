"""
Compute Engine Automator (Frame ID: 4.5)
Handles automation for the Compute Engine frame in WidgetInc.
"""

import time
import easyocr
import numpy as np
import pyautogui

from PIL import Image, ImageFilter, ImageGrab
from typing import Any, Dict

from automation.base_automator import BaseAutomator


class ComputeEngineAutomator(BaseAutomator):
    """Automation logic for Compute Engine (Frame 4.5)."""

    def __init__(self, frame_data: Dict[str, Any]):
        super().__init__(frame_data)
        # Initialize OCR reader for math equations
        self.ocr_reader = easyocr.Reader(["en"])
        self.allowed_chars = "0123456789x/-+=?"

    def preprocess_equation_image(self, image):
        """Extract white pixels and create clean image for OCR."""
        img_processed = Image.new("RGB", image.size, (0, 0, 0))

        # Keep only white pixels (#ffffff)
        for x in range(image.width):
            for y in range(image.height):
                pixel = image.getpixel((x, y))
                if pixel == (255, 255, 255):
                    img_processed.putpixel((x, y), (255, 255, 255))

        return img_processed

    def read_equation(self, equation_bbox):
        """Read math equation from screen area."""
        # Capture equation area
        equation_image = ImageGrab.grab(bbox=equation_bbox, all_screens=True)

        # Preprocess for OCR
        processed_image = self.preprocess_equation_image(equation_image)

        # Apply optimal blur
        img_test = processed_image.convert("L")
        img_test = img_test.filter(ImageFilter.GaussianBlur(radius=0.8))

        # Run OCR
        results = self.ocr_reader.readtext(np.array(img_test), allowlist=self.allowed_chars)
        if results:
            # EasyOCR returns [(bbox, text, confidence), ...]
            bbox, text, confidence = results[0]
            return str(text), float(confidence)
        return "", 0.0

    def solve_equation(self, equation_text):
        """Solve the math equation and return result."""
        try:
            # Replace 'x' with '*' for multiplication and remove '?'
            equation_clean = equation_text.replace("x", "*").replace("?", "")

            # Only allow safe mathematical operations
            allowed_chars = set("0123456789+-*/()= ")
            if not all(c in allowed_chars for c in equation_clean):
                return None

            # Split by '=' and solve left side
            if "=" in equation_clean:
                left_side = equation_clean.split("=")[0].strip()
                result = eval(left_side)
                return int(result)
        except Exception:
            pass
        return None

    def run_automation(self):
        start_time = time.time()

        equation_bbox = self.frame_data["bbox"]["equation_bbox"]
        answer1_bbox = self.frame_data["bbox"]["answer1_bbox"]
        answer2_bbox = self.frame_data["bbox"]["answer2_bbox"]
        answer3_bbox = self.frame_data["bbox"]["answer3_bbox"]
        answer4_bbox = self.frame_data["bbox"]["answer4_bbox"]

        answer1 = self.frame_data["buttons"]["answer1"]
        answer2 = self.frame_data["buttons"]["answer2"]
        answer3 = self.frame_data["buttons"]["answer3"]
        answer4 = self.frame_data["buttons"]["answer4"]

        # Main automation loop
        while self.should_continue:
            if time.time() - start_time > self.max_run_time:
                break

            # Read and solve equation
            equation_text, _ = self.read_equation(equation_bbox)
            answer1_text, _ = self.read_equation(answer1_bbox)
            answer2_text, _ = self.read_equation(answer2_bbox)
            answer3_text, _ = self.read_equation(answer3_bbox)
            answer4_text, _ = self.read_equation(answer4_bbox)

            answer = self.solve_equation(equation_text)
            clicked = False

            if answer is not None:
                self.logger.info(f"Equation: {equation_text} = {answer}")

                # Compare solved answer with each answer option
                answers = [
                    (answer1_text, answer1),
                    (answer2_text, answer2),
                    (answer3_text, answer3),
                    (answer4_text, answer4),
                ]

                for answer_text, button_data in answers:
                    try:
                        answer_value = int(answer_text)
                        if answer_value == answer:
                            self.logger.info(f"Found matching answer: {answer_value}")
                            pyautogui.click(button_data[0], button_data[1])
                            clicked = True
                            break
                    except ValueError:
                        continue

            # If no solution found or no matching answer, click random answer
            if not clicked:
                import random

                random_button = random.choice([answer1, answer2, answer3, answer4])
                pyautogui.click(random_button[0], random_button[1])
                self.logger.info("No valid answer found, clicked random answer")

            time.sleep(1)  # Prevent excessive CPU usage
