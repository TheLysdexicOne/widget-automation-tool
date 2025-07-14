# Widget Automation Tool - Task List

## Phase 1: Core Infrastructure

### Core Component (System Tray)

- [x] Create system tray icon and menu (Qt)
- [x] Implement application lifecycle management
- [x] Add context menu with options (Show Debug Console, Exit)
- [x] Handle application shutdown gracefully
- [x] Implement component coordination/messaging system
- [x] Add configuration loading/saving
- [x] Process detection for WidgetInc.exe

### Overlay Component

- [x] Create overlay window that stays on top
- [x] Implement window attachment to WidgetInc.exe
- [x] Draw 24x24 colored circle in 32x32 shaded box
- [x] Position overlay at top-right corner + 32px offset
- [x] Implement state-based color changes
- [x] Handle target window movement/resize
- [ ] Implement expanded and pinned state
  - On hover (0.25s) the screen expands into application (left, then down)
  - On click, the expanded screen is pinned and unpinned
- [x] Hide overlay when WidgetInc.exe is not found
- [x] Auto-reattach when WidgetInc.exe is launched

### Debug Console Component

- [x] Create main debug window with tabs
- [x] Implement Console tab with log display
- [x] Add Settings tab for configuration
- [x] Add Monitoring tab for process stats
- [x] Add Debug tab for advanced debugging
- [x] Implement log level dropdown (DEBUG, INFO, WARN, ERROR)
- [x] Add "Copy Logs" button functionality
- [x] Add "Close" button (minimize to tray)
- [x] Prevent application exit on console close
- [x] Auto-scroll log display
- [x] Log filtering by level/component

## Phase 2: Launch Parameters & Application Flow

### Command Line Arguments

- [x] Implement standard launch (no parameters)
- [x] Implement debug launch (--debug flag)
- [x] Implement test launch (--tests flag)
- [x] Add help documentation (--help)
- [x] Add version information (--version)

### Application States

- [x] Define application state enum/constants
- [x] Implement state change notifications
  - ACTIVE = performing automation
  - WAITING = valid screen/minigame and automation configuration found, waiting for user to start
  - INACTIVE = No automation configuration found for current screen/minigame
  - ERROR = Something wrong with application
- [x] Map states to overlay colors
- [x] Add state persistence across sessions
- [x] Implement state change logging

## Intermediate Phase 2.5

- [ ] Add contextual Show/Hide Console to right-click menu of system tray
- [ ] Add contextual Show/Hide Overlay to right-click menu of system tray

## Phase 3: Configuration & Settings

### Configuration System

- [ ] JSON configuration file structure
- [ ] Default settings initialization
- [ ] Settings validation
- [ ] Runtime settings updates
- [ ] Settings backup/restore
- [ ] User-specific vs system-wide settings

### Settings UI

- [ ] Overlay positioning settings
- [ ] Color scheme customization
- [ ] Log level preferences
- [ ] Auto-start options
- [ ] Process monitoring intervals
- [ ] Hotkey configuration

## Phase 4: Testing & Quality Assurance

### Unit Tests

- [ ] Core component tests
- [ ] Overlay component tests
- [ ] Debug console tests
- [ ] Configuration system tests
- [ ] State management tests

### Integration Tests

- [ ] Component communication tests
- [ ] Window attachment tests
- [ ] System tray integration tests
- [ ] Launch parameter tests

### Test Automation (--tests mode)

- [ ] Automated test runner
- [ ] Test result logging
- [ ] Performance benchmarking
- [ ] Memory leak detection
- [ ] Error condition simulation

## Phase 5: Advanced Features

### Process Monitoring

- [ ] Real-time process detection
- [ ] Process health monitoring
- [ ] Performance metrics collection
- [ ] Resource usage tracking
- [ ] Crash detection and logging

### Logging System

- [ ] Structured logging implementation
- [ ] Log rotation and archiving
- [ ] Remote logging capabilities
- [ ] Log analysis tools
- [ ] Error reporting system

### User Experience

- [ ] Tooltips and help text
- [ ] Error message improvements
- [ ] Performance optimizations
- [ ] Memory usage optimization
- [ ] Startup time improvements

## Phase 6: Documentation & Distribution

### Documentation

- [ ] User manual/guide
- [ ] API documentation
- [ ] Configuration reference
- [ ] Troubleshooting guide
- [ ] Developer documentation

### Distribution

- [ ] Executable packaging (PyInstaller)
- [ ] Installer creation
- [ ] Auto-update mechanism
- [ ] Version management
- [ ] Release notes
