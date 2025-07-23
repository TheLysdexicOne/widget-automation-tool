import time
from PyQt6.QtCore import QTimer


class UpdatePoller:
    """Utility to poll for global update signals and call a callback when updates are detected."""

    def __init__(self, update_key, callback, poll_interval=2000, parent=None):
        self.update_key = update_key
        self.callback = callback
        self.poll_interval = poll_interval
        self.last_check = 0.0
        self._timer = QTimer(parent)
        self._timer.timeout.connect(self._poll)

    def start(self):
        self._timer.start(self.poll_interval)

    def stop(self):
        self._timer.stop()

    def _poll(self):
        try:
            from utility.update_manager import UpdateManager

            update_manager = UpdateManager.instance()
            if update_manager.needs_update(self.update_key, self.last_check):
                self.callback()
                self.last_check = time.time()
        except Exception as e:
            pass
