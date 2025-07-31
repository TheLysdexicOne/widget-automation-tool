"""
Widget Automation Tool - Automation Module
Provides frame-specific automation capabilities for WidgetInc minigames.
"""

__version__ = "1.0.0"

from .automation_engine import AutomationEngine
from .automation_controller import AutomationController
from .base_automator import BaseAutomator
from .button_engine import ButtonEngine
from .global_hotkey_manager import GlobalHotkeyManager
from .scan_engine import ScanEngine

__all__ = [
    "AutomationEngine",
    "AutomationController",
    "BaseAutomator",
    "ButtonEngine",
    "GlobalHotkeyManager",
    "ScanEngine",
]
