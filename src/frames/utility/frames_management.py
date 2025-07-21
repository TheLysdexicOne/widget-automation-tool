"""
Frames Management - Core Data Operations

Handles frame data and screenshot storage operations:
- Frame database management (JSON-based)
- Screenshot storage and retrieval
- CRUD operations for frames

Following project standards: KISS, no duplicated calculations, modular design.
"""

import logging
import json
import uuid
import time
import shutil
from pathlib import Path
from typing import Dict, List, Optional

try:
    from PIL import Image

    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False

logger = logging.getLogger(__name__)


class FramesManagement:
    """Core data management for frames and screenshots."""

    def __init__(self, base_path: Path):
        self.base_path = base_path
        self.frames_db_path = base_path / "src" / "config" / "frames_database.json"
        self.screenshots_dir = base_path / "assets" / "screenshots"

        # Ensure directories exist
        self.frames_db_path.parent.mkdir(parents=True, exist_ok=True)
        self.screenshots_dir.mkdir(parents=True, exist_ok=True)

        self.frames_data = self._load_frames_database()

    def _load_frames_database(self) -> Dict:
        """Load frames database from JSON file."""
        if self.frames_db_path.exists():
            try:
                with open(self.frames_db_path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Error loading frames database: {e}")

        # Return default structure
        return {"frames": []}

    def _save_frames_database(self) -> bool:
        """Save frames database to JSON file."""
        try:
            # Create backup first
            if self.frames_db_path.exists():
                backup_path = self.frames_db_path.with_suffix(".json.backup")
                shutil.copy2(self.frames_db_path, backup_path)

            with open(self.frames_db_path, "w", encoding="utf-8") as f:
                json.dump(self.frames_data, f, indent=2, ensure_ascii=False)
            return True
        except Exception as e:
            logger.error(f"Error saving frames database: {e}")
            return False

    def get_frame_list(self) -> List[Dict]:
        """Get list of all frames."""
        return self.frames_data.get("frames", [])

    def get_frame_by_name(self, name: str) -> Optional[Dict]:
        """Get frame data by name."""
        for frame in self.frames_data.get("frames", []):
            if frame.get("name") == name:
                return frame
        return None

    def save_screenshot(self, screenshot: Image.Image, frame_name: Optional[str] = None) -> str:
        """Save screenshot and return UUID."""
        if not PIL_AVAILABLE:
            raise RuntimeError("PIL not available for screenshot operations")

        screenshot_uuid = str(uuid.uuid4())
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        filename = f"{timestamp}_{screenshot_uuid}.png"

        if frame_name:
            filename = f"{frame_name}_{filename}"

        screenshot_path = self.screenshots_dir / filename
        screenshot.save(screenshot_path)
        logger.info(f"Screenshot saved: {screenshot_path}")
        return screenshot_uuid

    def add_frame(self, frame_data: Dict) -> bool:
        """Add new frame to database."""
        try:
            self.frames_data["frames"].append(frame_data)
            return self._save_frames_database()
        except Exception as e:
            logger.error(f"Error adding frame: {e}")
            return False

    def update_frame(self, frame_name: str, frame_data: Dict) -> bool:
        """Update existing frame in database."""
        try:
            for i, frame in enumerate(self.frames_data["frames"]):
                if frame.get("name") == frame_name:
                    self.frames_data["frames"][i] = frame_data
                    return self._save_frames_database()
            return False
        except Exception as e:
            logger.error(f"Error updating frame: {e}")
            return False

    def delete_screenshot(self, screenshot_uuid: str) -> bool:
        """Delete screenshot file."""
        try:
            # Find and delete the file
            for screenshot_file in self.screenshots_dir.glob(f"*{screenshot_uuid}*"):
                screenshot_file.unlink()
                logger.info(f"Deleted screenshot: {screenshot_file}")
                return True
            return False
        except Exception as e:
            logger.error(f"Error deleting screenshot: {e}")
            return False

    def get_screenshot_data(self, screenshot_uuid: str) -> Optional[Dict]:
        """Get screenshot metadata. This is a placeholder implementation."""
        # For now, return basic data structure
        # In a full implementation, this might load from a metadata file
        return {"is_primary": False}  # Default implementation
