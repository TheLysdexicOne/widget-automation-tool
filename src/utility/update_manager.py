"""
Global Update Manager

Provides a simple global update notification system for the widget automation tool.
Allows different components to signal when data has changed and others to listen for updates.

Usage:
    # Signal an update
    UpdateManager.instance().signal_update("frames_data")

    # Check if update is needed
    if UpdateManager.instance().needs_update("frames_data", last_check_time):
        # Refresh your data
        last_check_time = time.time()
"""

import time
import logging
from typing import Dict, Set, Optional, List

logger = logging.getLogger(__name__)


class UpdateManager:
    """Singleton update manager for global state synchronization."""

    _instance = None

    def __init__(self):
        if UpdateManager._instance is not None:
            raise RuntimeError("UpdateManager is a singleton. Use UpdateManager.instance()")

        # Track when different data types were last updated
        self._update_times: Dict[str, float] = {}

        # Track which components are interested in which updates
        self._subscribers: Dict[str, Set[str]] = {}

        logger.debug("UpdateManager initialized")

    @classmethod
    def instance(cls) -> "UpdateManager":
        """Get the singleton instance."""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def signal_update(self, data_type: str, source: str = "unknown"):
        """Signal that a specific type of data has been updated."""
        current_time = time.time()
        self._update_times[data_type] = current_time

        logger.debug(f"Update signaled: {data_type} from {source} at {current_time}")

    def needs_update(self, data_type: str, last_check_time: float) -> bool:
        """Check if data needs to be refreshed based on last check time."""
        if data_type not in self._update_times:
            return False  # No updates have been signaled for this data type

        return self._update_times[data_type] > last_check_time

    def get_last_update_time(self, data_type: str) -> float:
        """Get the timestamp of the last update for a data type."""
        return self._update_times.get(data_type, 0.0)

    def subscribe(self, component_id: str, data_types: list):
        """Subscribe a component to updates for specific data types."""
        for data_type in data_types:
            if data_type not in self._subscribers:
                self._subscribers[data_type] = set()
            self._subscribers[data_type].add(component_id)

        logger.debug(f"Component {component_id} subscribed to updates: {data_types}")

    def unsubscribe(self, component_id: str, data_types: list | None = None):
        """Unsubscribe a component from updates."""
        if data_types is None:
            # Unsubscribe from all
            for subscribers in self._subscribers.values():
                subscribers.discard(component_id)
        else:
            for data_type in data_types:
                if data_type in self._subscribers:
                    self._subscribers[data_type].discard(component_id)

        logger.debug(f"Component {component_id} unsubscribed from updates")

    def get_subscribers(self, data_type: str) -> Set[str]:
        """Get all components subscribed to a data type."""
        return self._subscribers.get(data_type, set()).copy()

    def clear_all(self):
        """Clear all update times and subscriptions (mainly for testing)."""
        self._update_times.clear()
        self._subscribers.clear()
        logger.debug("All update data cleared")
