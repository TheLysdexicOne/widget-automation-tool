"""
Frames Manager - Core Data Management

Handles frame data and screenshot storage:
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
    import win32gui
    from PIL import Image, ImageGrab

    WIN32_AVAILABLE = True
except ImportError:
    WIN32_AVAILABLE = False

from PyQt6.QtWidgets import QDialog, QMessageBox
from PyQt6.QtGui import QPixmap

from .widgets.frames_dialog import FramesDialog
from .widgets.add_frame_dialog import AddFrameDialog
from .widgets.attach_frame_dialog import AttachToFrameDialog
from .widgets.edit_frames_dialog import EditFramesDialog

logger = logging.getLogger(__name__)


class FramesManager:
    """Manages frame data and screenshot storage."""

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


class FramesMenuSystem:
    """Main system for managing frames functionality."""

    def __init__(self, parent_widget, frames_manager: FramesManager):
        self.parent = parent_widget
        self.frames_manager = frames_manager
        self.logger = logging.getLogger(__name__)

    def show_frames_menu(self):
        """Show the main FRAMES menu - now simplified to just open the comprehensive dialog."""
        # Directly show the comprehensive frames dialog
        frames_list = self.frames_manager.get_frame_list()
        if not frames_list:
            QMessageBox.information(
                self.parent,
                "No Frames",
                "No frames available. Create a frame first using 'Add New Frame'.",
            )
            return
        dialog = FramesDialog(frames_list, self.frames_manager, self.parent)
        dialog.exec()

    def _show_frames_dialog(self):
        """Show comprehensive frames management dialog."""
        frames_list = self.frames_manager.get_frame_list()
        if not frames_list:
            QMessageBox.information(
                self.parent,
                "No Frames",
                "No frames available. Create a frame first using 'Add New Frame'.",
            )
            return
        dialog = FramesDialog(frames_list, self.frames_manager, self.parent)
        dialog.exec()

    def _show_add_frame_dialog(self):
        """Show Add New Frame dialog."""
        self.logger.info("Opening Add New Frame dialog")

        # Capture screenshot
        screenshot = self._capture_playable_screenshot()
        if not screenshot:
            QMessageBox.warning(self.parent, "Error", "Failed to capture screenshot")
            return

        # Show dialog
        dialog = AddFrameDialog(screenshot, self.parent.playable_coords, self.parent)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self._save_new_frame(dialog.get_frame_data(), screenshot)

    def _show_attach_frame_dialog(self):
        """Show Attach to Frame dialog."""
        self.logger.info("Opening Attach to Frame dialog")

        # Get existing frames
        frames_list = self.frames_manager.get_frame_list()
        if not frames_list:
            QMessageBox.information(
                self.parent,
                "No Frames",
                "No frames available. Create a frame first using 'Add New Frame'.",
            )
            return

        # Capture screenshot
        screenshot = self._capture_playable_screenshot()
        if not screenshot:
            QMessageBox.warning(self.parent, "Error", "Failed to capture screenshot")
            return

        # Show dialog
        dialog = AttachToFrameDialog(screenshot, frames_list, self.parent)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            selected_frame = dialog.get_selected_frame()
            if selected_frame:
                # Convert QPixmap to PIL Image and save screenshot
                screenshot_path = Path.cwd() / "temp_attach_screenshot.png"
                screenshot.save(str(screenshot_path))
                pil_image = Image.open(screenshot_path)

                # Save screenshot and get UUID
                screenshot_uuid = self.frames_manager.save_screenshot(pil_image, selected_frame.get("name", "unnamed"))

                # Attach to frame
                self._attach_screenshot_to_frame(selected_frame.get("name"), screenshot_uuid)

                # Clean up temp file
                screenshot_path.unlink()

    def _show_edit_frames_dialog(self):
        """Show Edit Frames dialog."""
        self.logger.info("Opening Edit Frames dialog")

        # Get existing frames
        frames_list = self.frames_manager.get_frame_list()
        if not frames_list:
            QMessageBox.information(
                self.parent,
                "No Frames",
                "No frames available. Create a frame first using 'Add New Frame'.",
            )
            return

        # Show dialog
        dialog = EditFramesDialog(frames_list, self.frames_manager.screenshots_dir, self.parent)

        if dialog.exec() == QDialog.DialogCode.Accepted:
            frame_name, modified_data, screenshots_to_delete = dialog.get_modified_data()
            if frame_name and modified_data:
                self._save_frame_changes(frame_name, modified_data, screenshots_to_delete)

    def _capture_playable_screenshot(self) -> Optional[QPixmap]:
        """Capture screenshot of playable area using window-specific capture."""
        try:
            # Get playable area coordinates
            playable = self.parent.playable_coords
            if not playable or not all(k in playable for k in ["x", "y", "width", "height"]):
                self.logger.warning("Invalid playable coordinates, using fallback")
                return self._capture_fallback_screenshot()

            self.logger.info(f"Capturing screenshot of playable area: {playable}")

            # Method 1: Try direct coordinate capture with explicit all_screens=True
            try:
                self.logger.info("Attempting direct coordinate capture with all_screens=True")
                screenshot = ImageGrab.grab(
                    bbox=(
                        playable["x"],
                        playable["y"],
                        playable["x"] + playable["width"],
                        playable["y"] + playable["height"],
                    ),
                    all_screens=True,  # Explicitly capture from all screens including negative coords
                )

                self.logger.info(f"Direct capture successful, size: {screenshot.size}")

                # Verify we got the right size
                if screenshot.size == (playable["width"], playable["height"]):
                    # Convert to QPixmap
                    screenshot_path = Path.cwd() / "temp_screenshot.png"
                    screenshot.save(screenshot_path)

                    # Verify the image has content
                    if screenshot.getbbox() is not None:
                        pixmap = QPixmap(str(screenshot_path))
                        self.logger.info(f"Direct capture QPixmap size: {pixmap.width()}x{pixmap.height()}")
                        screenshot_path.unlink()  # Clean up temp file
                        return pixmap
                    else:
                        self.logger.warning("Direct capture image appears empty")
                        screenshot_path.unlink()
                else:
                    self.logger.warning(
                        f"Direct capture size mismatch: got {screenshot.size}, expected ({playable['width']}, {playable['height']})"
                    )

            except Exception as e:
                self.logger.warning(f"Direct coordinate capture failed: {e}")

            # Method 2: Window-specific capture if we have hwnd
            if WIN32_AVAILABLE and self.parent.target_hwnd:
                try:
                    self.logger.info("Attempting window-specific capture")

                    # Bring window to foreground first
                    win32gui.SetForegroundWindow(self.parent.target_hwnd)

                    time.sleep(0.3)  # Longer delay for window activation

                    # Get window rectangle
                    window_rect = win32gui.GetWindowRect(self.parent.target_hwnd)
                    self.logger.info(f"Window rectangle: {window_rect}")

                    # Capture the entire window first
                    window_screenshot = ImageGrab.grab(bbox=window_rect, all_screens=True)

                    # Calculate relative coordinates within the window
                    # playable coords are absolute, window_rect gives us window position
                    rel_x = playable["x"] - window_rect[0]
                    rel_y = playable["y"] - window_rect[1]

                    self.logger.info(
                        f"Relative playable coords: ({rel_x}, {rel_y}) {playable['width']}x{playable['height']}"
                    )

                    # Crop to playable area
                    if (
                        rel_x >= 0
                        and rel_y >= 0
                        and rel_x + playable["width"] <= window_screenshot.width
                        and rel_y + playable["height"] <= window_screenshot.height
                    ):
                        playable_screenshot = window_screenshot.crop(
                            (
                                rel_x,
                                rel_y,
                                rel_x + playable["width"],
                                rel_y + playable["height"],
                            )
                        )

                        # Convert to QPixmap
                        screenshot_path = Path.cwd() / "temp_screenshot.png"
                        playable_screenshot.save(screenshot_path)

                        if playable_screenshot.getbbox() is not None:
                            pixmap = QPixmap(str(screenshot_path))
                            self.logger.info(f"Window capture successful: {pixmap.width()}x{pixmap.height()}")
                            screenshot_path.unlink()
                            return pixmap
                        else:
                            screenshot_path.unlink()

                    else:
                        self.logger.warning("Playable area extends outside window bounds")

                except Exception as e:
                    self.logger.warning(f"Window-specific capture failed: {e}")

            # Fall back to full screen approach
            self.logger.warning("All capture methods failed, using fallback")
            return self._capture_fallback_screenshot()

        except Exception as e:
            self.logger.error(f"Error in screenshot capture: {e}")
            return self._capture_fallback_screenshot()

    def _capture_fallback_screenshot(self) -> Optional[QPixmap]:
        """Fallback screenshot capture of entire screen for testing."""
        try:
            self.logger.info("Using fallback screenshot capture (entire screen)")

            # Capture entire screen
            screenshot = ImageGrab.grab()

            # Scale down for dialog display
            screenshot = screenshot.resize((800, 600), Image.Resampling.LANCZOS)

            # Convert to QPixmap
            screenshot_path = Path.cwd() / "temp_fallback_screenshot.png"
            screenshot.save(screenshot_path)

            pixmap = QPixmap(str(screenshot_path))
            self.logger.info(f"Fallback screenshot size: {pixmap.width()}x{pixmap.height()}")

            screenshot_path.unlink()  # Clean up temp file

            return pixmap

        except Exception as e:
            self.logger.error(f"Error in fallback screenshot capture: {e}")
            return None

    def _save_new_frame(self, frame_data: Dict, screenshot: QPixmap):
        """Save new frame with screenshot."""
        try:
            # Convert QPixmap to PIL Image for saving
            screenshot_path = Path.cwd() / "temp_frame_screenshot.png"
            screenshot.save(str(screenshot_path))
            pil_image = Image.open(screenshot_path)

            # Save screenshot and get UUID
            screenshot_uuid = self.frames_manager.save_screenshot(pil_image, frame_data["name"])

            # Add screenshot UUID to frame data
            frame_data["screenshots"] = [screenshot_uuid]

            # Save frame to database
            if self.frames_manager.add_frame(frame_data):
                QMessageBox.information(
                    self.parent,
                    "Success",
                    f"Frame '{frame_data['name']}' saved successfully!",
                )
                self.logger.info(f"New frame created: {frame_data['name']}")
            else:
                QMessageBox.warning(self.parent, "Error", "Failed to save frame to database")

            # Clean up temp file
            screenshot_path.unlink()

        except Exception as e:
            self.logger.error(f"Error saving new frame: {e}")
            QMessageBox.warning(self.parent, "Error", f"Failed to save frame: {str(e)}")

    def _attach_screenshot_to_frame(self, frame_name: str, screenshot_uuid: str):
        """Attach screenshot to existing frame."""
        try:
            frames_data = self.frames_manager.get_frame_list()
            for frame_data in frames_data:
                if frame_data.get("name") == frame_name:
                    if "screenshots" not in frame_data:
                        frame_data["screenshots"] = []

                    if screenshot_uuid not in frame_data["screenshots"]:
                        frame_data["screenshots"].append(screenshot_uuid)

                        # Update frame in database
                        if self.frames_manager.update_frame(frame_name, frame_data):
                            QMessageBox.information(
                                self.parent,
                                "Success",
                                f"Screenshot attached to frame '{frame_name}' successfully!",
                            )
                            self.logger.info(f"Screenshot attached to frame: {frame_name}")
                            return True
                        else:
                            QMessageBox.warning(
                                self.parent,
                                "Error",
                                "Failed to update frame in database",
                            )
                            return False
                    else:
                        QMessageBox.information(
                            self.parent,
                            "Info",
                            "Screenshot already attached to this frame.",
                        )
                        return True

            QMessageBox.warning(self.parent, "Error", f"Frame '{frame_name}' not found")
            return False

        except Exception as e:
            self.logger.error(f"Error attaching screenshot to frame: {e}")
            QMessageBox.warning(self.parent, "Error", f"Failed to attach screenshot: {str(e)}")
            return False

    def _save_frame_changes(self, original_name: str, updated_data: Dict, screenshots_to_delete: List[str]):
        """Save changes to existing frame."""
        try:
            # Delete marked screenshots first
            for uuid_to_delete in screenshots_to_delete:
                try:
                    self.frames_manager.delete_screenshot(uuid_to_delete)
                    self.logger.info(f"Deleted screenshot: {uuid_to_delete}")
                except Exception as e:
                    self.logger.warning(f"Could not delete screenshot {uuid_to_delete}: {e}")

            # Update frame data (name might have changed)
            if self.frames_manager.update_frame(original_name, updated_data):
                # If name changed, we need to update the key
                if original_name != updated_data.get("name"):
                    # This is handled by the update_frame method in FramesManager
                    pass

                QMessageBox.information(
                    self.parent,
                    "Success",
                    f"Frame '{updated_data.get('name')}' updated successfully!",
                )
                self.logger.info(f"Frame updated: {original_name} -> {updated_data.get('name')}")
                return True
            else:
                QMessageBox.warning(self.parent, "Error", "Failed to update frame in database")
                return False

        except Exception as e:
            self.logger.error(f"Error saving frame changes: {e}")
            QMessageBox.warning(self.parent, "Error", f"Failed to save changes: {str(e)}")
            return False
