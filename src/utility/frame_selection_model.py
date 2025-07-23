from PyQt6.QtCore import QObject, pyqtSignal


class FrameSelectionModel(QObject):
    """Singleton model to synchronize frame selection across dialogs."""

    selection_changed = pyqtSignal(dict)

    _instance = None

    def __init__(self):
        super().__init__()
        self._selected_frame = None
        self._frames_list = []

    @classmethod
    def instance(cls):
        if cls._instance is None:
            cls._instance = FrameSelectionModel()
        return cls._instance

    def set_frames_list(self, frames_list):
        self._frames_list = frames_list

    def get_frames_list(self):
        return self._frames_list

    def set_selected_frame(self, frame):
        self._selected_frame = frame
        self.selection_changed.emit(frame)

    def get_selected_frame(self):
        return self._selected_frame
