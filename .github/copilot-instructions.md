# Widget Automation Tool: AI Coding Agent Instructions

## Essential Architecture Knowledge

### Core Principles

- **KISS** - "Keep It Simple Stupid": Manual selection beats unreliable detection
- **DRY** - "Don't Repeat Yourself": Extract common automation patterns to shared utilities
- **Workflow** - "Make it Work, Make it Right, Make it Fast": Focus on function before form
- **Clean Functional Design** - Don't go overboard on looks until application functions correctly
- **Virtual Environment is Absolute Must** - Everything needed is in the virtual environment, no global installs

### Code Style & Comments

- **If the code explains itself, don't use comments**
- **Exception:** Categorization comment headers for functions are encouraged (e.g., `# ==============================`)
- **Exception:** Triple quotes for docstrings explaining a function as a whole

### Core Components & Data Flow

- **CacheManager (`utility/cache_manager.py`)** - Centralized window detection & caching. Get via `get_cache_manager()` singleton
- **AutomationController (`automation/automation_controller.py`)** - Orchestrates threading & frame automator lifecycle
- **MainWindow (`main.py`)** - PyQt6 overlay that snaps to WidgetInc window, creates frame buttons dynamically from database
- **Frame Automators (`automation/frame_automators/tier_*/`)** - Individual automation scripts inheriting from `BaseAutomator`

### Database & Caching Pattern

- Frames database: `config/database/frames_database.json` → `frames.cache` (screen coords)
- CacheManager auto-generates cache from database, validates every 5s with database file watching
- **Three coordinate systems**: Grid (user-friendly) → Screen (absolute) → Frame (relative)
- **Database validation is necessary** - User edits JSON, corruption breaks coordinate translation
- **Never edit frames.cache directly** - it's auto-generated from frames_database.json

## Development Commands & Workflows

### Environment Setup

```bash
# Always use this sequence for terminal commands:
.\venv.bat    # NOT ".venv\Scripts\activate"
python src\main.py --debug    # Debug mode shows console output
.\start.bat   # Production mode (INFO+ only to console)
```

### Threading & UI Patterns

- AutomationController manages threads via `start_automation(frame_data)` → creates daemon thread
- UI callbacks: `set_ui_callback()` for failsafe events, `set_completion_callback()` for cleanup
- Global hotkeys (right-click/spacebar) trigger `stop_all_automations()` → emergency thread cleanup

## Error Handling Philosophy

**Smart Fail-Fast (Not Defensive Programming):**

- **Required imports MUST work** - Don't try/except around missing dependencies:

```python
# Good - let it fail if missing:
import pyautogui
import win32gui

# Bad - don't do this:
try:
    import pyautogui
except ImportError:
    pyautogui = None  # WHY?!
```

- **Avoid excessive try/except blocks** - Most AI/LLM overuse try-except where it's not needed
- **Let the application crash on logic errors** - Fix the root cause, don't mask it
- **Database corruption is an exception** - We DO validate database structure because:
  - `frames_database.json` (user-editable) → `frames.cache` (auto-generated)
  - CacheManager translates grid system → screen coordinates → frame coordinates
  - Invalid data here breaks the entire coordinate system

**When to use try/except:**

```python
# Good - file operations, user input, external systems:
try:
    with open(config_file) as f:
        config = json.load(f)
except FileNotFoundError:
    config = default_config()

# Bad - basic logic that should always work:
try:
    button_data = frame["automation"]["button_data"]
    x, y, color = button_data  # If this fails, data is corrupt - let it crash!
except:
    x, y, color = 0, 0, "red"  # Don't mask data corruption
```

### Project-Specific Conventions

#### Button Creation

- To create a button:
  ```python
  button_name = self.create_button("button_name")
  ```

#### Single Point Interactions

- For single point interactions:
  ```python
  interaction_name = self.frame_data["interactions"]["interaction_name"]
  ```

#### Bounding Boxes (BBoxes)

- For bounding box coordinates:
  ```python
  bbox_name = self.frame_data["bbox"]["bbox_name"]
  ```

#### Colors

- For color or color sets:
  ```python
  color_name = self.frame_data["colors"]["color_name"]
  colors_name = self.frame_data["colors"]["colors_name"]
  ```

#### Frame Coordinates (frame_xy)

- If frame coordinates are needed (e.g., for overlays or relative positioning):
  ```python
  bbox_name = self.frame_data["frame_xy"]["bbox"]["bbox_name"]
  ```

#### Screenshot Helpers (utility/window_utils.py)

- To capture the full frame area:
  ```python
  img = get_frame_screenshot()
  ```
- To capture a specific bounding box:
  ```python
  img = get_cropped_bbox_of_frame_screenshot(bbox)
  ```

#### Coordinate Conversion Helpers (utility/coordinate_utils.py)

- Use the helpers in `utility/coordinate_utils.py` for converting between grid, screen, and frame coordinates. Example usage:

  ```python
  from utility.coordinate_utils import (
      conv_frame_percent_to_frame_coords,
      conv_frame_percent_to_screen_coords,
      conv_frame_coords_to_frame_percent,
      conv_frame_coords_to_screen_coords,
      conv_screen_coords_to_frame_coords,
      conv_screen_coords_to_frame_percent,
      conv_frame_percent_to_screen_bbox,
      fp_to_fc_coord,
      fp_to_sc_coord,
      fc_to_fp_coord,
      fc_to_sc_coord,
      sc_to_fc_coord,
      sc_to_fp_coord,
      fp_to_sc_bbox,
  )

  # Frame percent to frame coords
  frame_x, frame_y = conv_frame_percent_to_frame_coords(percent_x, percent_y)

  # Frame percent to screen coords
  screen_x, screen_y = conv_frame_percent_to_screen_coords(percent_x, percent_y)

  # Frame coords to frame percent
  percent_x, percent_y = conv_frame_coords_to_frame_percent(frame_x, frame_y)

  # Frame coords to screen coords
  screen_x, screen_y = conv_frame_coords_to_screen_coords(frame_x, frame_y)

  # Screen coords to frame coords
  frame_x, frame_y = conv_screen_coords_to_frame_coords(screen_x, screen_y)

  # Screen coords to frame percent
  percent_x, percent_y = conv_screen_coords_to_frame_percent(screen_x, screen_y)

  # Frame percent bbox to screen bbox
  screen_bbox = conv_frame_percent_to_screen_bbox((x1, y1, x2, y2))

  # Shorthand functions (aliases)
  frame_x, frame_y = fp_to_fc_coord(percent_x, percent_y)
  screen_x, screen_y = fp_to_sc_coord(percent_x, percent_y)
  percent_x, percent_y = fc_to_fp_coord(frame_x, frame_y)
  screen_x, screen_y = fc_to_sc_coord(frame_x, frame_y)
  frame_x, frame_y = sc_to_fc_coord(screen_x, screen_y)
  percent_x, percent_y = sc_to_fp_coord(screen_x, screen_y)
  screen_bbox = fp_to_sc_bbox((x1, y1, x2, y2))
  ```

---

### Logging System (New Timestamped Approach)

- **Every startup creates new log file**: `widget_YYYYMMDD_HHMMSS.log`
- **Debug always logged to file**, console shows INFO+ (normal) or DEBUG+ (debug mode)
- Auto-compression after 5 files, use `setup_logging()` from `utility/logging_utils.py`

### PyQt6 Styling Approach

- **Minimal CSS unless explicitly requested** - use native PyQt6 styling
- Window snapping via CacheManager signals: `window_found.connect()`, `window_lost.connect()`
- Frameless overlay with `Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint`

### File Organization Reality

```
src/main.py                          # Main PyQt6 overlay application
src/automation/
├── automation_controller.py         # Thread management & automator lifecycle
├── automation_engine.py            # Common automation utilities (clicks, scans)
├── base_automator.py               # Abstract base for frame automators
└── frame_automators/tier_*/        # Individual frame automation modules
src/utility/
├── cache_manager.py                # Window detection & coordinate caching
├── window_utils.py                 # Helper functions using CacheManager
├── coordinate_utils.py             # Coordinate conversion helpers
└── logging_utils.py                # Timestamped logging with compression
tools/tracker.py                    # Standalone coordinate tracking tool
```

Use `semantic_search` to find automation patterns, coordinate usage, or threading examples in the codebase.

# Ongoing Development for Frame Detector

**Unless explicity told, AI is to not alter this file.**

## Key Principles

- KISS and DRY
- Start simple and work towards complex. Sometimes the simple solutions work best.
- Don't try to do too much at once. It'll just end in disaster.

## Design Philosophy

- There is **NO AUTOSTART**
  - Under no circumstance should the application auto-start any programmed automation on a frame.
- For now, the start button will be about 1/4 up the frame centered. This may vary frame-to-frame _later_.
- In the end, it will only be displayed on frames that have automation programmed.
- Once activated, it will transform, but for now, we shrink it to a small green orb attached to (0, 32) of the frame itself

## Prompt Analysis over time

---
