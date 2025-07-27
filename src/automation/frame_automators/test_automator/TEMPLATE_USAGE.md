# Automator Template Usage Guide

## Quick Start

1. **Copy the template:**

   ```bash
   cp template_automator.py your_frame_automator.py
   ```

2. **Update the class name and docstring:**

   ```python
   class YourFrameAutomator(BaseAutomator):
       """Automation logic for Your Frame (Frame X.X)."""
   ```

3. **Define your buttons:**

   ```python
   button_names = ["button1", "button2", "button3"]
   buttons = [self.button_manager.get_button(name) for name in button_names]
   ```

4. **Implement your logic in `run_automation()`**

## Template Patterns

### Pattern 1: Simple Button Clicking (Iron Mine Style)

```python
def run_automation(self):
    button_names = ["action1", "action2", "action3"]
    buttons = [self.button_manager.get_button(name) for name in button_names]

    while self.is_running and not self.should_stop:
        for button in buttons:
            if self.engine.is_button_active(button):
                self.engine.click_button(button)  # Built-in safety
                self.safe_sleep(self.click_delay)

        if not self.safe_sleep(self.cycle_delay):
            break
```

### Pattern 2: Timed Automation (Iron Smelter Style)

```python
def run_automation(self):
    import time  # Add this import
    start_time = time.time()
    action_button = self.button_manager.get_button("action")

    while self.is_running and not self.should_stop:
        if time.time() - start_time > self.max_run_time:
            break

        if self.engine.is_button_active(action_button):
            self.engine.click_button(action_button)  # Built-in safety
            self.safe_sleep(self.click_delay)

        if not self.safe_sleep(self.cycle_delay):
            break
```

### Pattern 3: State Detection with Failure Handling

```python
def run_automation(self):
    buttons = [self.button_manager.get_button(name) for name in ["btn1", "btn2"]]
    failed_count = 0

    while self.is_running and not self.should_stop:
        success = False

        for button in buttons:
            if self.engine.is_button_active(button):
                self.engine.click_button(button)  # Built-in safety
                self.safe_sleep(self.click_delay)
                success = True

        if not success:
            failed_count += 1
            if failed_count >= 5:
                self.log_info("No available actions - stopping")
                break
        else:
            failed_count = 0

        if not self.safe_sleep(self.cycle_delay):
            break
```

## Available Methods

### From BaseAutomator:

- `self.log_info(message)` - Log info messages
- `self.log_debug(message)` - Log debug messages
- `self.log_error(message)` - Log error messages
- `self.safe_sleep(duration)` - Sleep with interrupt checking
- `self.button_manager.get_button(name)` - Get button data
- `self.check_button_failsafe(button, name)` - Manual failsafe check

### From AutomationEngine:

- `self.engine.is_button_active(button)` - Check if button is clickable
- `self.engine.is_button_inactive(button)` - Check if button is disabled
- `self.engine.click_button(button, name)` - Click with built-in validation
- `self.engine.failsafe_color_validation(...)` - Advanced validation

### Timing Constants (Override in `__init__` if needed):

- `self.max_run_time = 300` - Default 5 minutes
- `self.click_delay = 0.05` - 50ms after clicks
- `self.cycle_delay = 0.1` - 100ms between cycles
- `self.factory_delay = 0.5` - 500ms for slow operations

## Safety Features

### Built-in Safety (Automatic):

- Every `click_button()` validates frame automatically
- Immediate stop if wrong frame detected (cat scenario!)
- No manual failsafe checks needed in normal automation

### Manual Safety (When Needed):

```python
# Check specific button before complex operations
if not self.check_button_failsafe(button, "button_name"):
    return  # Will trigger failsafe and stop automation
```

## Best Practices

1. **Always end loops with `safe_sleep`** for proper interruption
2. **Use descriptive button names** in get_button() calls
3. **Log important state changes** with log_info()
4. **Handle failure states gracefully** (storage full, no actions available)
5. **Test timeout logic** if using time-based automation
6. **Keep automation logic simple** - focus on the core task

## Integration

Place your automator in the appropriate tier folder:

- `tier_1/` - Basic production frames
- `tier_2/` - Mid-tier frames
- `tier_X/` - Higher tier frames

Update the automation controller to recognize your new frame ID and automator class.
