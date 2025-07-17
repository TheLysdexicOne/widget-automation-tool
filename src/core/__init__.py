"""
Core module - Main application components.
"""

from .application import WidgetAutomationApp, ApplicationState
from .window_manager import WindowManager
from .mouse_tracker import MouseTracker

__all__ = ["WidgetAutomationApp", "ApplicationState", "WindowManager", "MouseTracker"]
