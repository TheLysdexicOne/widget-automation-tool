import os
import sys

from PIL import ImageGrab

sys.path.append(os.path.join(os.path.dirname(__file__), "..", "src"))
from utility.window_utils import get_cache_manager

_window_manager = get_cache_manager()
window_info = _window_manager.get_window_info()

frame_data = _window_manager.get_frame_data("5.3")

print(f"Frame Data: {frame_data}")
