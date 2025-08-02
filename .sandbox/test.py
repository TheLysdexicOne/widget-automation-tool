import easyocr
import numpy as np
from PIL import Image, ImageFilter


class PixelArtMathReader:
    """OCR reader optimized for pixel art math equations."""

    def __init__(self):
        self.reader = easyocr.Reader(["en"])
        self.allowed_chars = "0123456789x/-+=?"

    def preprocess_image(self, image_path):
        """Extract white pixels and create clean image."""
        img_original = Image.open(image_path).convert("RGB")
        img_processed = Image.new("RGB", img_original.size, (0, 0, 0))

        # Keep only white pixels (#ffffff)
        for x in range(img_original.width):
            for y in range(img_original.height):
                pixel = img_original.getpixel((x, y))
                if pixel == (255, 255, 255):
                    img_processed.putpixel((x, y), (255, 255, 255))

        return img_processed

    def test_blur_levels(self, image_path):
        """Test different Gaussian blur levels to find optimal OCR results."""
        img_processed = self.preprocess_image(image_path)
        results = []

        print("=== EasyOCR Gaussian Blur Test ===")
        for blur_level in range(5, 16):  # 0.5 to 1.5 in 0.1 increments
            blur_radius = blur_level / 10.0

            img_test = img_processed.convert("L")
            img_test = img_test.filter(ImageFilter.GaussianBlur(radius=blur_radius))

            ocr_results = self.reader.readtext(np.array(img_test), allowlist=self.allowed_chars)

            if ocr_results:
                text, confidence = ocr_results[0][1], ocr_results[0][2]
                print(f"Blur {blur_radius:.1f}: {text} | Confidence: {confidence:.2f}")
                results.append((text, confidence))
            else:
                print(f"Blur {blur_radius:.1f}: No text detected")

        return results

    def calculate_combined_confidence(self, results_list):
        """Calculate combined confidence starting from max and adding for confirmations."""
        if not results_list:
            return "", 0.0

        # Group by text content
        text_groups = {}
        for text, confidence in results_list:
            if text not in text_groups:
                text_groups[text] = []
            text_groups[text].append(confidence)

        # Find most common result
        most_common_text = max(text_groups.keys(), key=lambda x: len(text_groups[x]))
        matching_confidences = text_groups[most_common_text]

        # Start with max confidence and add bonus for each additional confirmation
        base_confidence = max(matching_confidences)

        # Add bonus for each confirming result (diminishing returns)
        bonus = 0.0
        for i, conf in enumerate(sorted(matching_confidences)[1:], 1):  # Skip the max
            bonus += (conf * 0.01) / i  # Diminishing bonus per confirmation

        combined_confidence = min(1.0, base_confidence + bonus)

        return most_common_text, combined_confidence

    def read_text(self, image_path):
        """Read text from pixel art image with optimal settings."""
        img_processed = self.preprocess_image(image_path)

        # Use optimal blur level (adjust based on your testing)
        img_test = img_processed.convert("L")
        img_test = img_test.filter(ImageFilter.GaussianBlur(radius=0.8))

        results = self.reader.readtext(np.array(img_test), allowlist=self.allowed_chars)

        if results:
            return results[0][1], results[0][2]
        return "", 0.0


if __name__ == "__main__":
    reader = PixelArtMathReader()

    # Test different blur levels
    results = reader.test_blur_levels(".sandbox/text.png")

    # Calculate combined confidence
    if results:
        best_text, combined_confidence = reader.calculate_combined_confidence(results)
        print(f"\n=== Final Result ===")
        print(f"Text: '{best_text}' | Combined Confidence: {combined_confidence:.2f}")

    # Single read with optimal settings
    text, confidence = reader.read_text(".sandbox/text.png")
    print(f"Single Read: '{text}' | Confidence: {confidence:.2f}")
