"""
Border Analysis Engine - Core image processing for frame border analysis

Analyzes left and right borders of frames to extract unique characteristics:
- Color analysis (average, dominant colors, variance)
- Pattern detection for border identification
- Signature generation for frame matching

Border Regions:
- Left Border: 5% inset from left edge, 20% center strip
- Right Border: 5% inset from right edge, 20% center strip

Following project standards: KISS, efficient image processing, numpy-based operations.
"""

import hashlib
import logging
from datetime import datetime
from typing import Dict, List, Tuple, Any, Optional

import numpy as np

import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from utility.window_utils import get_frame_screenshot
from utility.cache_manager import get_cache_manager

logger = logging.getLogger(__name__)


class BorderAnalysisEngine:
    """Core engine for analyzing frame borders"""

    def __init__(self):
        self.border_inset = 0.05  # 5% inset from edges
        self.center_strip = 0.20  # 20% center strip height
        self.cache_manager = get_cache_manager()

    def analyze_frame_borders(self, frame_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze left and right borders of a frame

        Args:
            frame_data: Frame data from database

        Returns:
            dict: Analysis results including color data and signatures
        """
        # Get frame screenshot
        screenshot = get_frame_screenshot()
        if screenshot is None:
            raise Exception("Failed to capture frame screenshot")

        # Get frame area for metadata
        frame_area = self.cache_manager.get_frame_area()
        if not frame_area:
            raise Exception("No frame area available")

        # Convert to numpy array for processing
        img_array = np.array(screenshot)
        height, width = img_array.shape[:2]

        # Calculate border regions
        left_border = self._extract_left_border(img_array, width, height)
        right_border = self._extract_right_border(img_array, width, height)

        # Analyze each border
        left_analysis = self._analyze_border_strip(left_border, "left")
        right_analysis = self._analyze_border_strip(right_border, "right")

        # Create result structure
        result = {
            "frame_id": frame_data.get("id", "unknown"),
            "frame_name": frame_data.get("name", "unknown"),
            "resolution": f"{frame_area['width']}x{frame_area['height']}",
            "screen_position": f"{frame_area['x']},{frame_area['y']}",
            "left_border": left_analysis,
            "right_border": right_analysis,
            "combined_signature": self._create_combined_signature(left_analysis, right_analysis),
            "timestamp": datetime.now().isoformat(),
            "analysis_parameters": {
                "border_inset": self.border_inset,
                "center_strip": self.center_strip,
                "border_dimensions": {
                    "left": f"{left_border.shape[1]}x{left_border.shape[0]}",
                    "right": f"{right_border.shape[1]}x{right_border.shape[0]}",
                },
            },
        }

        logger.info(f"Analyzed borders for frame: {frame_data.get('name', 'unknown')}")
        return result

    def _extract_left_border(self, img_array: np.ndarray, width: int, height: int) -> np.ndarray:
        """Extract left border strip (5% inset, 20% center)"""
        # Calculate dimensions
        inset_width = int(width * self.border_inset)
        strip_height = int(height * self.center_strip)

        # Calculate center position
        center_y = height // 2
        start_y = center_y - strip_height // 2
        end_y = start_y + strip_height

        # Extract border region
        border_strip = img_array[start_y:end_y, 0:inset_width]
        return border_strip

    def _extract_right_border(self, img_array: np.ndarray, width: int, height: int) -> np.ndarray:
        """Extract right border strip (5% inset, 20% center)"""
        # Calculate dimensions
        inset_width = int(width * self.border_inset)
        strip_height = int(height * self.center_strip)

        # Calculate center position
        center_y = height // 2
        start_y = center_y - strip_height // 2
        end_y = start_y + strip_height

        # Extract border region (from right edge)
        start_x = width - inset_width
        border_strip = img_array[start_y:end_y, start_x:width]
        return border_strip

    def _analyze_border_strip(self, border_strip: np.ndarray, side: str) -> Dict[str, Any]:
        """
        Analyze a border strip to extract characteristics

        Args:
            border_strip: Numpy array of border pixels
            side: "left" or "right" for identification

        Returns:
            dict: Analysis results for this border
        """
        # Flatten to get all pixel values
        pixels = border_strip.reshape(-1, 3)

        # Basic color statistics
        average_color = [int(pixels[:, i].mean()) for i in range(3)]
        color_variance = float(np.var(pixels))

        # Dominant colors (top 5)
        unique_colors, counts = np.unique(pixels, axis=0, return_counts=True)
        sorted_indices = np.argsort(counts)[::-1]  # Sort by frequency
        dominant_colors = [unique_colors[i].tolist() for i in sorted_indices[:5]]

        # Color distribution analysis
        color_ranges = self._analyze_color_ranges(pixels)

        # Edge analysis
        edge_characteristics = self._analyze_edges(border_strip)

        # Generate signature
        signature = self._generate_border_signature(
            average_color, dominant_colors, color_variance, edge_characteristics
        )

        return {
            "side": side,
            "dimensions": f"{border_strip.shape[1]}x{border_strip.shape[0]}",
            "average_color": average_color,
            "color_variance": color_variance,
            "dominant_colors": dominant_colors,
            "color_ranges": color_ranges,
            "edge_characteristics": edge_characteristics,
            "signature": signature,
            "pixel_count": len(pixels),
        }

    def _analyze_color_ranges(self, pixels: np.ndarray) -> Dict[str, Any]:
        """Analyze color distribution and ranges"""
        # RGB channel statistics
        r_stats = {"min": int(pixels[:, 0].min()), "max": int(pixels[:, 0].max()), "std": float(pixels[:, 0].std())}
        g_stats = {"min": int(pixels[:, 1].min()), "max": int(pixels[:, 1].max()), "std": float(pixels[:, 1].std())}
        b_stats = {"min": int(pixels[:, 2].min()), "max": int(pixels[:, 2].max()), "std": float(pixels[:, 2].std())}

        # Color diversity (unique colors / total pixels)
        unique_colors = len(np.unique(pixels, axis=0))
        diversity = unique_colors / len(pixels)

        # Brightness analysis
        brightness = np.mean(pixels, axis=1)
        brightness_stats = {
            "average": float(brightness.mean()),
            "min": float(brightness.min()),
            "max": float(brightness.max()),
            "std": float(brightness.std()),
        }

        return {
            "red": r_stats,
            "green": g_stats,
            "blue": b_stats,
            "diversity": float(diversity),
            "unique_colors": unique_colors,
            "brightness": brightness_stats,
        }

    def _analyze_edges(self, border_strip: np.ndarray) -> Dict[str, Any]:
        """Analyze edge patterns in the border strip"""
        # Convert to grayscale for edge detection
        gray = np.mean(border_strip, axis=2)

        # Simple edge detection using gradient
        grad_x = np.abs(np.gradient(gray, axis=1))
        grad_y = np.abs(np.gradient(gray, axis=0))
        edge_magnitude = np.sqrt(grad_x**2 + grad_y**2)

        # Edge statistics
        edge_density = float(np.mean(edge_magnitude))
        edge_variance = float(np.var(edge_magnitude))
        max_edge = float(np.max(edge_magnitude))

        # Pattern detection (simplified)
        # Check for horizontal/vertical line patterns
        horizontal_edges = np.mean(grad_y)
        vertical_edges = np.mean(grad_x)

        return {
            "edge_density": edge_density,
            "edge_variance": edge_variance,
            "max_edge_strength": max_edge,
            "horizontal_tendency": float(horizontal_edges),
            "vertical_tendency": float(vertical_edges),
            "edge_ratio": float(horizontal_edges / max(vertical_edges, 0.001)),  # Avoid division by zero
        }

    def _generate_border_signature(
        self,
        average_color: List[int],
        dominant_colors: List[List[int]],
        color_variance: float,
        edge_characteristics: Dict[str, Any],
    ) -> str:
        """Generate a unique signature for the border"""
        # Create signature components
        signature_data = {
            "avg": average_color,
            "dom": dominant_colors[:3],  # Top 3 dominant colors
            "var": round(color_variance, 2),
            "edge_den": round(edge_characteristics["edge_density"], 2),
            "edge_ratio": round(edge_characteristics["edge_ratio"], 2),
        }

        # Convert to string and hash
        signature_str = str(signature_data)
        signature_hash = hashlib.md5(signature_str.encode()).hexdigest()

        return signature_hash

    def _create_combined_signature(self, left_analysis: Dict[str, Any], right_analysis: Dict[str, Any]) -> str:
        """Create a combined signature from both borders"""
        combined_data = {
            "left_sig": left_analysis["signature"],
            "right_sig": right_analysis["signature"],
            "left_avg": left_analysis["average_color"],
            "right_avg": right_analysis["average_color"],
            "variance_diff": abs(left_analysis["color_variance"] - right_analysis["color_variance"]),
        }

        combined_str = str(combined_data)
        return hashlib.sha256(combined_str.encode()).hexdigest()

    def compare_signatures(self, sig1: str, sig2: str) -> float:
        """
        Compare two signatures and return similarity score

        Args:
            sig1: First signature
            sig2: Second signature

        Returns:
            float: Similarity score (0.0 = identical, 1.0 = completely different)
        """
        if sig1 == sig2:
            return 0.0

        # Convert hex strings to integers for comparison
        try:
            int1 = int(sig1, 16)
            int2 = int(sig2, 16)

            # Calculate Hamming distance (XOR then count bits)
            xor_result = int1 ^ int2
            bit_differences = bin(xor_result).count("1")

            # Normalize by total possible bits (assuming 256-bit hashes)
            max_bits = len(sig1) * 4  # Each hex char = 4 bits
            similarity = bit_differences / max_bits

            return min(1.0, similarity)  # Cap at 1.0

        except ValueError:
            # If conversion fails, use simple string comparison
            return 1.0 if sig1 != sig2 else 0.0

    def validate_frame_detection(
        self, target_signature: str, candidate_signatures: List[str], threshold: float = 0.1
    ) -> Tuple[bool, Optional[str]]:
        """
        Validate frame detection using border signatures

        Args:
            target_signature: Signature to match
            candidate_signatures: List of possible matches
            threshold: Maximum difference to consider a match

        Returns:
            tuple: (is_match, best_match_signature or None)
        """
        best_score = float("inf")
        best_match = None

        for candidate in candidate_signatures:
            score = self.compare_signatures(target_signature, candidate)
            if score < best_score:
                best_score = score
                best_match = candidate

        is_match = best_score <= threshold
        return is_match, best_match if is_match else None
