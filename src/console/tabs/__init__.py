"""
Console tabs package.
"""

from .base_tab import BaseTab
from .console_tab import ConsoleTab
from .settings_tab import SettingsTab
from .monitoring_tab import MonitoringTab
from .debug_tab import DebugTab

__all__ = ["BaseTab", "ConsoleTab", "SettingsTab", "MonitoringTab", "DebugTab"]
