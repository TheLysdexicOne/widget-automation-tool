"""
Configuration Manager

Handles loading, saving, and managing application configuration.
"""

import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional


class ConfigManager:
    """Manages application configuration."""

    def __init__(self, config_dir: Optional[Path] = None):
        self.logger = logging.getLogger(__name__)

        # Set config directory
        if config_dir is None:
            # Use the config directory in the project root
            self.config_dir = Path(__file__).parent.parent.parent / "config"
        else:
            self.config_dir = Path(config_dir)

        self.config_dir.mkdir(exist_ok=True)

        # Config files
        self.settings_file = self.config_dir / "settings.json"
        self.minigames_file = self.config_dir / "minigames.json"

        # Current configuration
        self.settings = {}
        self.minigames = {}

        # Load configuration
        self._load_configuration()

    def _load_configuration(self):
        """Load configuration from files."""
        try:
            # Load settings
            self.settings = self._load_json_file(
                self.settings_file, self._get_default_settings()
            )

            # Load minigames configuration
            self.minigames = self._load_json_file(
                self.minigames_file, self._get_default_minigames()
            )

            self.logger.info("Configuration loaded successfully")

        except Exception as e:
            self.logger.error(f"Failed to load configuration: {e}")
            # Use defaults
            self.settings = self._get_default_settings()
            self.minigames = self._get_default_minigames()

    def _load_json_file(self, file_path: Path, default_data: Dict) -> Dict:
        """Load JSON data from file with fallback to defaults."""
        try:
            if file_path.exists():
                with open(file_path, "r", encoding="utf-8") as f:
                    data = json.load(f)

                # Merge with defaults to ensure all keys exist
                merged_data = default_data.copy()
                merged_data.update(data)
                return merged_data
            else:
                # Create file with defaults
                self._save_json_file(file_path, default_data)
                return default_data

        except Exception as e:
            self.logger.error(f"Error loading {file_path}: {e}")
            return default_data

    def _save_json_file(self, file_path: Path, data: Dict):
        """Save JSON data to file."""
        try:
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            self.logger.error(f"Error saving {file_path}: {e}")

    def _get_default_settings(self) -> Dict[str, Any]:
        """Get default application settings."""
        return {
            "overlay": {
                "size": {"circle_diameter": 24, "box_size": 32},
                "position": {"anchor": "top-right", "offset_x": 0, "offset_y": 32},
                "colors": {
                    "active": "#00FF00",  # Green
                    "waiting": "#FFFF00",  # Yellow
                    "inactive": "#808080",  # Gray
                    "error": "#FF0000",  # Red
                },
                "opacity": 0.8,
                "always_on_top": True,
            },
            "process_monitor": {
                "target_process": "WidgetInc.exe",
                "check_interval": 1000,
                "auto_attach": True,
            },
            "debug_console": {
                "log_level": "INFO",
                "max_log_lines": 1000,
                "auto_scroll": True,
                "window_size": {"width": 800, "height": 600},
            },
            "system_tray": {"show_notifications": True, "minimize_on_close": True},
            "general": {
                "auto_start": False,
                "check_for_updates": True,
                "log_to_file": True,
            },
        }

    def _get_default_minigames(self) -> Dict[str, Any]:
        """Get default minigames configuration."""
        return {
            "mining": {
                "enabled": True,
                "automation_enabled": False,
                "detection": {
                    "window_title_contains": ["mining", "mine"],
                    "ui_elements": [],
                },
                "actions": {"click_positions": [], "key_sequences": []},
            },
            "crafting": {
                "enabled": True,
                "automation_enabled": False,
                "detection": {
                    "window_title_contains": ["craft", "workshop"],
                    "ui_elements": [],
                },
                "actions": {"click_positions": [], "key_sequences": []},
            },
        }

    def get_setting(self, key_path: str, default=None):
        """Get a setting value using dot notation (e.g., 'overlay.colors.active')."""
        try:
            keys = key_path.split(".")
            value = self.settings

            for key in keys:
                value = value[key]

            return value

        except (KeyError, TypeError):
            return default

    def set_setting(self, key_path: str, value: Any):
        """Set a setting value using dot notation."""
        try:
            keys = key_path.split(".")
            current = self.settings

            # Navigate to the parent of the target key
            for key in keys[:-1]:
                if key not in current:
                    current[key] = {}
                current = current[key]

            # Set the value
            current[keys[-1]] = value

            # Save settings
            self.save_settings()

        except Exception as e:
            self.logger.error(f"Error setting config value {key_path}: {e}")

    def get_minigame_config(self, minigame_name: str) -> Dict[str, Any]:
        """Get configuration for a specific minigame."""
        return self.minigames.get(minigame_name, {})

    def save_settings(self):
        """Save current settings to file."""
        self._save_json_file(self.settings_file, self.settings)

    def save_minigames(self):
        """Save current minigames configuration to file."""
        self._save_json_file(self.minigames_file, self.minigames)

    def reload_configuration(self):
        """Reload configuration from files."""
        self._load_configuration()

    def get_overlay_colors(self) -> Dict[str, str]:
        """Get overlay color configuration."""
        return self.get_setting(
            "overlay.colors",
            {
                "active": "#00FF00",
                "waiting": "#FFFF00",
                "inactive": "#808080",
                "error": "#FF0000",
            },
        )
