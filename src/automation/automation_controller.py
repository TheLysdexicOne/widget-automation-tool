"""
Automation Controller
Orchestrates automation execution and manages frame automators.
"""

import importlib
import logging
import re
import threading
from typing import Any, Dict, Optional

from .frame_automators.base_automator import BaseAutomator


class AutomationController:
    """Controls and manages automation for different frames."""

    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.active_automators: Dict[str, BaseAutomator] = {}
        self.automation_threads: Dict[str, threading.Thread] = {}
        self.frame_mapping = self._build_frame_mapping()
        self.ui_callback = None  # Callback for UI events (failsafe, etc.)
        self.completion_callback = None  # Callback for automation completion

    def _build_frame_mapping(self) -> Dict[str, str]:
        """Build mapping from frame ID to module name based on frames database."""
        # This mapping is built from the frames_database.json structure
        mapping = {
            # Tier 1
            "1.1": "iron_mine",
            "1.2": "iron_smelter",
            "1.3": "widget_factory",
            # Tier 2
            "2.1": "sand_pit",
            "2.2": "glass_kiln",
            "2.3": "gyroscope_fabricator",
            "2.4": "widget_spinner",
            # Tier 3
            "3.1": "oil_field",
            "3.2": "oil_power_plant",
            "3.3": "battery_assembler",
            "3.4": "capacitor_bank",
            # Tier 4
            "4.1": "copper_mine",
            "4.2": "copper_forge",
            "4.3": "plastic_extractor",
            "4.4": "circuit_fab",
            "4.5": "computational_engine",
            # Tier 5
            "5.1": "tesla_coil",
            "5.2": "core_foundry",
            "5.3": "integrator",
            # Tier 6
            "6.1": "silicon_extruder",
            "6.2": "processor_lab",
            "6.3": "mainframe_assembler",
            "6.4": "graveyard",
            # Tier 7
            "7.1": "uranium_mine",
            "7.2": "fuel_rod_assembler",
            "7.3": "nuclear_power_plant",
            "7.4": "cloud_digitizer",
            # Tier 8
            "8.1": "widget_minitizers",
            "8.2": "nanoscale_lab",
            "8.3": "reactor_foundry",
            "8.4": "quantum_tunneler",
            "8.5": "incinerator",
            # Tier 9
            "9.1": "helium_extractor",
            "9.2": "conductor_foundry",
            "9.3": "ai_laboratory",
            "9.4": "ai_delimiter",
            # Tier 10
            "10.1": "training_center",
            "10.2": "data_transformer",
            "10.3": "ascension_facility",
            # Tier 11
            "11.1": "perpetual_motion_engine",
            "11.2": "sentience_facility",
            "11.3": "picoscale_lab",
            "11.4": "sentience_aggregator",
            # Tier 12
            "12.1": "omega_processor_lab",
            "12.2": "omega_core_foundry",
            "12.3": "omega_widget_distiller",
            "12.4": "omega_casing_factory",
            "12.5": "omega_shielding_plant",
            "12.6": "omega_project_assembler",
            # Tier 13
            "13.1": "rocket_electronics_lab",
            "13.2": "rocket_fuel_distiller",
            "13.3": "rocket_part_assembler",
            "13.4": "omega_launch_factory",
        }
        return mapping

    def set_ui_callback(self, callback):
        """Set the UI callback function for automation events."""
        self.ui_callback = callback

    def get_automator(self, frame_data: Dict[str, Any]) -> Optional[BaseAutomator]:
        """Get automator instance for the given frame."""
        frame_id = frame_data.get("id", "")

        # Check if already have active automator
        if frame_id in self.active_automators:
            return self.active_automators[frame_id]

        try:
            # Get module name from mapping
            module_name = self.frame_mapping.get(frame_id)
            if not module_name:
                self.logger.warning(f"No module mapping found for frame ID: {frame_id}")
                return None

            # Parse tier from frame ID
            tier_match = re.match(r"(\d+)\.\d+", frame_id)
            if not tier_match:
                self.logger.error(f"Invalid frame ID format: {frame_id}")
                return None

            tier_num = tier_match.group(1)

            # Dynamic import
            module_path = f"automation.frame_automators.tier_{tier_num}.{module_name}"
            module = importlib.import_module(module_path)

            # Get the automator class (following naming convention)
            class_name = f"{self._to_class_name(module_name)}Automator"
            automator_class = getattr(module, class_name)

            # Create and cache automator instance
            automator = automator_class(frame_data)
            self.active_automators[frame_id] = automator

            self.logger.info(f"Created automator for {frame_id}: {class_name}")
            return automator

        except Exception as e:
            self.logger.error(f"Failed to load automator for {frame_id}: {e}")
            return None

    def _to_class_name(self, module_name: str) -> str:
        """Convert module name to class name (e.g., 'iron_mine' -> 'IronMine')."""
        return "".join(word.capitalize() for word in module_name.split("_"))

    def start_automation(self, frame_data: Dict[str, Any]) -> bool:
        """Start automation for the given frame in a background thread."""
        frame_id = frame_data.get("id")
        if not frame_id:
            self.logger.error("Frame data missing ID")
            return False

        try:
            # Stop any existing automation for this frame
            if frame_id in self.automation_threads:
                self.stop_automation(frame_id)

            # Get the automator
            automator = self.get_automator(frame_data)
            if not automator:
                self.logger.error(f"Failed to get automator for frame: {frame_id}")
                return False

            # Set the UI callback on the automator for failsafe events
            automator.set_ui_callback(self.ui_callback)

            # Create and start the automation thread
            automation_thread = threading.Thread(
                target=self._run_automation_thread,
                args=(frame_id, automator),
                daemon=True,
                name=f"Automation-{frame_id}",
            )

            self.automation_threads[frame_id] = automation_thread
            automation_thread.start()

            self.logger.info(f"Started automation thread for frame: {frame_id}")
            return True

        except Exception as e:
            self.logger.error(f"Failed to start automation for {frame_id}: {e}")
            return False

    def set_completion_callback(self, callback):
        """Set callback for automation completion events."""
        self.completion_callback = callback

    def _run_automation_thread(self, frame_id: str, automator: BaseAutomator):
        """Run the automation in a background thread."""
        try:
            self.logger.info(f"Automation thread starting for {frame_id}")
            # Call the automator's start_automation method
            automator.start_automation()
            self.logger.info(f"Automation completed for {frame_id}")
        except Exception as e:
            self.logger.error(f"Automation error for {frame_id}: {e}")
        finally:
            # Clean up when automation finishes
            self._cleanup_automation(frame_id)

            # Notify UI that automation completed
            if self.completion_callback:
                try:
                    self.completion_callback(frame_id)
                except Exception as e:
                    self.logger.error(f"Error calling completion callback: {e}")

    def _cleanup_automation(self, frame_id: str):
        """Clean up automation resources."""
        try:
            if frame_id in self.automation_threads:
                del self.automation_threads[frame_id]

            # Remove from active automators
            if frame_id in self.active_automators:
                del self.active_automators[frame_id]

            self.logger.info(f"Cleaned up automation thread for {frame_id}")
        except Exception as e:
            self.logger.error(f"Error cleaning up automation for {frame_id}: {e}")

    def stop_automation(self, frame_id: str) -> bool:
        """Stop automation for the given frame ID."""
        try:
            automator = self.active_automators.get(frame_id)
            if automator:
                # Call the automator's stop_automation method
                automator.stop_automation()

                self.logger.info(f"Requested stop for automation: {frame_id}")

                # Wait for thread to finish (with timeout)
                thread = self.automation_threads.get(frame_id)
                if thread and thread.is_alive():
                    thread.join(timeout=5.0)  # 5 second timeout
                    if thread.is_alive():
                        self.logger.warning(f"Automation thread for {frame_id} did not stop within timeout")

                # Clean up and trigger completion callback
                self._cleanup_automation(frame_id)

                # Always trigger completion callback to reset UI
                if self.completion_callback:
                    try:
                        self.completion_callback(frame_id)
                    except Exception as e:
                        self.logger.error(f"Error calling completion callback: {e}")

                return True
            else:
                self.logger.warning(f"No active automator found for frame: {frame_id}")
                return False

        except Exception as e:
            self.logger.error(f"Failed to stop automation for {frame_id}: {e}")
            return False

    def is_automation_running(self, frame_id: str) -> bool:
        """Check if automation is currently running for the given frame ID."""
        automator = self.active_automators.get(frame_id)
        if not automator:
            return False
        return automator.is_running

    def stop_all_automations(self) -> bool:
        """Stop all active automations."""
        success = True
        for frame_id, automator in self.active_automators.items():
            if not automator.stop_automation():
                self.logger.error(f"Failed to stop automation for frame {frame_id}")
                success = False

        return success

    def get_status(self) -> Dict[str, Any]:
        """Get status of all automators."""
        status = {"active_count": len(self.active_automators), "automators": {}}

        for frame_id, automator in self.active_automators.items():
            status["automators"][frame_id] = automator.get_status()

        return status
