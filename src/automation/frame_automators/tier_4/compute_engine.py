"""
Compute Engine Automator (Frame ID: 4.5)
Handles automation for the Compute Engine frame in WidgetInc.
"""

import easyocr
import numpy as np
import pyautogui
import re
import ast
import operator as _op
from PIL import Image, ImageFilter, ImageGrab
from typing import Any, Dict, Tuple

from automation.base_automator import BaseAutomator


class ComputeEngineAutomator(BaseAutomator):
    """Automation logic for Compute Engine (Frame 4.5)."""

    def __init__(self, frame_data: Dict[str, Any]):
        super().__init__(frame_data)
        # Initialize OCR reader for math equations
        self.ocr_reader = easyocr.Reader(["en"], gpu=False)
        self.allowed_chars = "0123456789x/-+=?"  # limited charset speeds up OCR
        # Precompile regex
        self._cleanup_re = re.compile(r"[^0-9x+\-*/=()]")
        # Predefine safe eval operators
        self._ops = {ast.Add: _op.add, ast.Sub: _op.sub, ast.Mult: _op.mul, ast.Div: _op.floordiv}

    # ==============================
    # Image / OCR Helpers
    # ==============================
    def _vector_preprocess(self, pil_img: Image.Image) -> Image.Image:
        """Vectorized keep-white-only preprocessing (much faster than pixel loops)."""
        arr = np.asarray(pil_img.convert("RGB"))
        mask = np.all(arr == 255, axis=2)
        out = np.zeros_like(arr)
        out[mask] = 255
        return Image.fromarray(out)

    def _ocr_image(self, pil_img: Image.Image) -> str:
        """Run OCR on preprocessed image; return first text segment or empty string."""
        if not self.should_continue:
            return ""
        # Convert to grayscale + slight blur for smoothing edges
        g = pil_img.convert("L").filter(ImageFilter.GaussianBlur(radius=0.6))
        # detail=0 returns only text list (faster) but we sometimes want 1st candidate only
        results = self.ocr_reader.readtext(np.array(g), allowlist=self.allowed_chars, detail=0, paragraph=False)
        if results:
            return str(results[0])[:32]
        return ""

    def _capture_and_crop_batch(self, bboxes: Dict[str, Tuple[int, int, int, int]]) -> Dict[str, Image.Image]:
        """Capture ONE bounding grab covering all regions then crop each to reduce grabs."""
        # Expand list of bboxes
        coords = list(bboxes.values())
        x1 = min(b[0] for b in coords)
        y1 = min(b[1] for b in coords)
        x2 = max(b[2] for b in coords)
        y2 = max(b[3] for b in coords)
        full = ImageGrab.grab(bbox=(x1, y1, x2, y2), all_screens=True)
        out = {}
        for name, (bx1, by1, bx2, by2) in bboxes.items():
            out[name] = full.crop((bx1 - x1, by1 - y1, bx2 - x1, by2 - y1))
        return out

    # ==============================
    # Equation Solving
    # ==============================
    def _safe_eval(self, expr: str) -> int | None:
        """Safely evaluate integer arithmetic expression using AST (no eval)."""
        try:
            node = ast.parse(expr, mode="eval").body

            def _eval(n):
                if isinstance(n, ast.BinOp) and type(n.op) in self._ops:
                    return self._ops[type(n.op)](_eval(n.left), _eval(n.right))
                if isinstance(n, ast.UnaryOp) and isinstance(n.op, (ast.UAdd, ast.USub)):
                    val = _eval(n.operand)
                    return val if isinstance(n.op, ast.UAdd) else -val
                if isinstance(n, ast.Num):  # py<3.8 compatibility style
                    if isinstance(n.n, (int, float)):
                        return int(n.n)
                    raise ValueError
                if isinstance(n, ast.Constant):  # py>=3.8
                    if isinstance(n.value, (int, float)):
                        return int(n.value)
                    raise ValueError
                raise ValueError

            return int(_eval(node))
        except Exception:
            return None

    def solve_equation(self, equation_text: str):
        """Solve the math equation and return result (int) or None."""
        if not equation_text:
            return None
        # Normalize
        eq = equation_text.replace("x", "*")
        eq = self._cleanup_re.sub("", eq)
        if "=" in eq:
            eq = eq.split("=")[0]
        eq = eq.strip()
        if not eq:
            return None
        return self._safe_eval(eq)

    # ==============================
    # Main Automation
    # ==============================
    def run_automation(self):
        # Retrieve bboxes (assumed screen absolute already)
        b = self.frame_data["bbox"]
        equation_bbox = b["equation_bbox"]
        answer_bboxes = {
            "answer1": b["answer1_bbox"],
            "answer2": b["answer2_bbox"],
            "answer3": b["answer3_bbox"],
            "answer4": b["answer4_bbox"],
        }
        # Button coord tuples (frame percent converted upstream)
        buttons = self.frame_data["buttons"]
        ans_buttons = [buttons["answer1"], buttons["answer2"], buttons["answer3"], buttons["answer4"]]

        # Pre-create int coords for buttons
        ans_buttons = [(int(x), int(y)) for (x, y, *_) in ans_buttons]

        while self.should_continue:
            # Batch capture all answer/equation regions in one grab
            if not self.should_continue:
                break
            batch = self._capture_and_crop_batch({"equation": equation_bbox, **answer_bboxes})
            if not self.should_continue:
                break
            eq_img = self._vector_preprocess(batch["equation"]) if self.should_continue else None
            ans_imgs = (
                [self._vector_preprocess(batch[f"answer{i}"]) for i in range(1, 5)] if self.should_continue else []
            )
            if not self.should_continue:
                break
            eq_text = self._ocr_image(eq_img) if eq_img is not None else ""
            answers_text = [self._ocr_image(img) for img in ans_imgs] if self.should_continue else []
            if not self.should_continue:
                break
            solved = self.solve_equation(eq_text)

            clicked = False
            if solved is not None:
                # Try direct match
                for txt, (bx, by) in zip(answers_text, ans_buttons):
                    try:
                        if int(txt) == solved:
                            self.log_info(f"Equation {eq_text} = {solved} -> clicking answer")
                            pyautogui.click(bx, by)
                            clicked = True
                            break
                    except (ValueError, TypeError):
                        continue

            if not clicked:
                # Fallback random choice (avoid heavy import every loop)
                import random

                bx, by = random.choice(ans_buttons)
                pyautogui.click(bx, by)
                self.log_debug("No valid answer match; random answer clicked")

            if not self.sleep(1):  # modest delay
                break
