"""
Status Manager - Application State Logic

This module handles the intelligent detection and management of application states
based on actual capabilities and current context.
"""

import logging
from enum import Enum
from typing import Optional
from PyQt6.QtCore import QObject, pyqtSignal, QTimer


class ApplicationState(Enum):
    """Application state tracking with 5-state system from task list."""

    ACTIVE = "active"  # Performing automation
    READY = (
        "ready"  # Tool recognizes current screen/minigame, waiting for user to activate
    )
    ATTENTION = "attention"  # Tool recognizes current screen/minigame, but no automation programmed
    INACTIVE = "inactive"  # Tool does not recognize current screen/minigame, no automation available
    ERROR = "error"  # Something wrong with application


class StatusManager(QObject):
    """Manages application state detection and transitions."""

    # Signals
    state_changed = pyqtSignal(ApplicationState)

    def __init__(self):
        super().__init__()
        self.logger = logging.getLogger(__name__)
        self.current_state = ApplicationState.INACTIVE

        # Capabilities tracking
        self.has_scene_recognition = False
        self.has_automation_logic = False
        self.target_window_found = False
        self.win32_available = False

        # Reset animation state
        self.reset_animation_timer = None
        self.animation_states = [
            ApplicationState.ERROR,
            ApplicationState.INACTIVE,
            ApplicationState.ATTENTION,
            ApplicationState.READY,
            ApplicationState.ACTIVE,
        ]
        self.animation_index = 0
        self.animation_target_state = None

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
        self._detect_current_state()

    def _detect_current_state(self) -> ApplicationState:
        """Detect the actual current state based on capabilities and context."""
        try:
            # ERROR state - something is fundamentally wrong
            if not self.win32_available:
                new_state = ApplicationState.ERROR
                reason = "WIN32 API not available"

            # INACTIVE state - tool doesn't recognize current screen/minigame
            elif not self.target_window_found:
                new_state = ApplicationState.INACTIVE
                reason = "Target window (WidgetInc.exe) not found"

            # With current capabilities, we can only be INACTIVE or ERROR
            # since we don't have scene recognition yet
            elif not self.has_scene_recognition:
                new_state = ApplicationState.INACTIVE
                reason = (
                    "No scene recognition - cannot determine current screen/minigame"
                )

            # Future states (not reachable with current code):
            # ATTENTION - recognizes screen but no automation programmed
            # READY - recognizes screen and has automation, waiting for user
            # ACTIVE - currently performing automation
            else:
                # This branch won't be reached until we implement scene recognition
                new_state = ApplicationState.ATTENTION
                reason = "Scene recognized but no automation implemented"

            if new_state != self.current_state:
                old_state = self.current_state
                self.current_state = new_state
                self.state_changed.emit(new_state)
                self.logger.info(
                    f"State changed: {old_state.value} -> {new_state.value} ({reason})"
                )

            return new_state

        except Exception as e:
            self.logger.error(f"Error detecting state: {e}")
            return ApplicationState.ERROR

    def start_initialization_sequence(self):
        """Start the initialization sequence with animation and status detection."""
        self.logger.info("Starting initialization sequence")
        self._start_status_sequence(is_initialization=True)

    def start_reset_sequence(self):
        """Start the reset sequence with animation and status re-detection."""
        self.logger.info("Starting status reset sequence")
        self._start_status_sequence(is_initialization=False)

    def _start_status_sequence(self, is_initialization: bool = False):
        """Start the unified status sequence (initialization or reset)."""
        if self.reset_animation_timer and self.reset_animation_timer.isActive():
            self.logger.debug("Status sequence already running")
            return

        sequence_type = "initialization" if is_initialization else "reset"
        self.logger.info(f"Starting {sequence_type} status sequence")

        self.animation_index = 0
        self.animation_target_state = None  # Will be determined after re-detection

        # Create timer for animation
        self.reset_animation_timer = QTimer()
        self.reset_animation_timer.timeout.connect(self._animation_step)
        self.reset_animation_timer.start(500)  # 0.5 seconds per state

        # Start with first animation state
        self._animation_step()

    def start_reset_animation(self):
        """Legacy method - now calls the unified reset sequence."""
        self.start_reset_sequence()

    def _animation_step(self):
        """Execute one step of the status sequence animation."""
        if self.animation_index < len(self.animation_states):
            # Show current animation state (cosmetic)
            anim_state = self.animation_states[self.animation_index]
            self.state_changed.emit(anim_state)
            self.logger.debug(
                f"Animation step {self.animation_index + 1}: {anim_state.value}"
            )
            self.animation_index += 1

        else:
            # Animation complete - now do the actual work
            self.reset_animation_timer.stop()
            self.reset_animation_timer = None

            self.logger.info("Animation complete, re-evaluating actual status...")

            # Force re-detection of the actual state
            # This is where the real logic happens, not just cosmetic animation
            actual_state = self._detect_current_state()

            # Ensure UI is updated to show the final state (even if it's the same as before animation)
            self.state_changed.emit(actual_state)

            self.logger.info(
                f"Status sequence complete, actual state: {actual_state.value}"
            )

    def get_current_state(self) -> ApplicationState:
        """Get the current application state."""
        return self.current_state

    def force_state_detection(self):
        """Force a re-evaluation of the current state."""
        self._detect_current_state()
