"""
Status Manager - Application State Logic

Handles intelligent detection and management of application states
based on actual capabilities and current context.
"""

import logging
from enum import Enum
from PyQt6.QtCore import QObject, pyqtSignal


class ApplicationState(Enum):
    """Application state tracking with 5-state system."""

    ACTIVE = "active"  # Performing automation
    READY = "ready"  # Recognizes screen, waiting for user to activate
    ATTENTION = "attention"  # Recognizes screen, no automation programmed
    INACTIVE = "inactive"  # Doesn't recognize screen, no automation available
    ERROR = "error"  # Something wrong with application


class StatusManager(QObject):
    """Manages application state detection and transitions."""

    state_changed = pyqtSignal(ApplicationState)

    def __init__(self):
        super().__init__()
        self.logger = logging.getLogger(__name__)
        self.current_state = ApplicationState.INACTIVE

        # Capability tracking
        self.has_scene_recognition = False
        self.has_automation_logic = False
        self.target_window_found = False
        self.win32_available = False

    def update_capabilities(self, **kwargs):
        """Update capability flags that affect state detection."""
        if "scene_recognition" in kwargs:
            self.has_scene_recognition = kwargs["scene_recognition"]
        if "automation_logic" in kwargs:
            self.has_automation_logic = kwargs["automation_logic"]
        if "target_window" in kwargs:
            self.target_window_found = kwargs["target_window"]
        if "win32_available" in kwargs:
            self.win32_available = kwargs["win32_available"]

        # Recalculate state after capability update
        # Always emit signal to ensure UI synchronization
        self._detect_current_state(force_update=True)

    def _detect_current_state(self, force_update=False) -> ApplicationState:
        """Detect the current state based on capabilities and context."""
        try:
            # Determine state based on capabilities
            if not self.win32_available:
                new_state = ApplicationState.ERROR
                reason = "WIN32 API not available"
            elif not self.target_window_found:
                new_state = ApplicationState.ERROR
                reason = "Target window not found"
            elif not self.has_scene_recognition:
                new_state = ApplicationState.INACTIVE
                reason = "Target window found, but no scene recognition available"
            else:
                # We have both target window AND scene recognition
                if self.has_automation_logic:
                    new_state = ApplicationState.READY
                    reason = "Scene recognized, automation ready"
                else:
                    new_state = ApplicationState.ATTENTION
                    reason = "Scene recognized, no automation programmed"

            # Update state if changed OR if forced (for UI synchronization)
            if new_state != self.current_state or force_update:
                old_state = self.current_state
                self.current_state = new_state
                self.state_changed.emit(new_state)
                if new_state != old_state:  # Only log actual state changes
                    self.logger.info(f"State: {old_state.value} -> {new_state.value} ({reason})")
                elif force_update:
                    self.logger.debug(f"UI sync: {new_state.value} ({reason})")

            return new_state

        except Exception as e:
            self.logger.error(f"Error detecting state: {e}")
            new_state = ApplicationState.ERROR
            if new_state != self.current_state:
                self.current_state = new_state
                self.state_changed.emit(new_state)
            return new_state

    def get_current_state(self) -> ApplicationState:
        """Get the current application state."""
        return self.current_state

    def force_state_detection(self):
        """Force re-evaluation of the current state."""
        self._detect_current_state()
