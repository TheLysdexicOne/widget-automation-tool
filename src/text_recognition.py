from PIL import Image
import pytesseract

def extract_text(image: Image) -> str:
    """
    Extracts text from the given image using Optical Character Recognition (OCR).

    Args:
        image (Image): The image from which to extract text.

    Returns:
        str: The recognized text from the image.
    """
    text = pytesseract.image_to_string(image)
    return text.strip()