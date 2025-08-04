# Widget Automation Tool: AI Coding Agent Instructions

## Essential Architecture Knowledge

### Core Principles

- **KISS** - "Keep It Simple Stupid": Manual selection beats unreliable detection
- **DRY** - "Don't Repeat Yourself": Extract common automation patterns to shared utilities
- **Workflow** - "Make it Work, Make it Right, Make it Fast": Focus on function before form
- **Clean Functional Design** - Don't go overboard on looks until application functions correctly
- **Virtual Environment is Absolute Must** - Everything needed is in the virtual environment, no global installs

### Core Components & Data Flow

- **CacheManager (`utility/cache_manager.py`)** - Centralized window detection & caching. Get via `get_cache_manager()` singleton
- **AutomationController (`automation/automation_controller.py`)** - Orchestrates threading & frame automator lifecycle
- **MainWindow (`main.py`)** - PyQt6 overlay that snaps to WidgetInc window, creates frame buttons dynamically from database
- **Frame Automators (`automation/frame_automators/tier_*/`)** - Individual automation scripts inheriting from `BaseAutomator`

### Critical Coordinate System

- All coordinates are **frame-relative** (0,0 = top-left of game area), not screen coordinates
- Use `frame_to_screen_coords(x, y)` for clicks: `automation_engine.frame_click(frame_x, frame_y)`
- Screenshots: `ImageGrab.grab(...all_screens=True)` for multi-monitor support
- Grid system: 192x128 pixel art units, use `PIXEL_ART_GRID_WIDTH/HEIGHT` constants

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

### Key Automation Patterns

```python
# Frame automator template (inherit from BaseAutomator):
class MyFrameAutomator(BaseAutomator):
    def run_automation_sequence(self):
        # Use automation_engine methods:
        self.automation_engine.frame_click(x, y)
        self.automation_engine.button_active(button_data)

        # Coordinate conversion:
        screen_x, screen_y = frame_to_screen_coords(frame_x, frame_y)

        # Emergency stop check:
        if self.should_stop:
            return
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

## Project-Specific Conventions

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
└── logging_utils.py                # Timestamped logging with compression
tools/tracker.py                    # Standalone coordinate tracking tool
```

Use `semantic_search` to find automation patterns, coordinate usage, or threading examples in the codebase.
