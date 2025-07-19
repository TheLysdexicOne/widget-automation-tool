# Window Utilities - API Reference

The consolidated `src/utility/window_utils.py` provides comprehensive window management functionality.

## Available Functions

### Core Window Detection

- `find_target_process(target_process_name="WidgetInc.exe")` - Find process PID
- `find_window_by_pid(pid)` - Find window handle by process ID
- `is_window_valid(hwnd)` - Validate window handle
- `find_target_window(target_process_name="WidgetInc.exe")` - Complete detection pipeline

### Window Information

- `get_window_info(hwnd)` - Comprehensive window details (rect, client area, screen position)
- `get_client_area_coordinates(hwnd)` - Legacy compatibility for client area

### Coordinate Calculations

- `calculate_playable_area(window_info)` - 3:2 aspect ratio playable area
- `calculate_overlay_position(window_info, width, height, offset_x=-8, offset_y=40)` - Overlay positioning
- `calculate_playable_area_percentages(x, y, playable_area)` - Mouse position percentages

## Usage Examples

```python
from utility.window_utils import find_target_window, calculate_playable_area_percentages

# Complete target detection
target_info = find_target_window("WidgetInc.exe")
if target_info:
    window_info = target_info["window_info"]
    playable_area = target_info["playable_area"]

    # Calculate mouse position percentages
    mouse_info = calculate_playable_area_percentages(500, 300, playable_area)
    if mouse_info["inside_playable"]:
        print(f"Mouse at {mouse_info['x_percent']:.1f}%, {mouse_info['y_percent']:.1f}%")
```

## Migration Notes

- Old `target_window_utils.py` functionality merged here
- Legacy `window_utils.py` compatibility functions included
- All applications updated to import from `utility.window_utils`
