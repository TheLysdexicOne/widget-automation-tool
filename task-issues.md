# Widget Automation Tool - Issues List

## Open

## Closed

- [x] Overlay positioned incorrectly
  - Top-right of the overlay should be anchored to the top-right of the window, offset down 32px to be below the header of the application.
- [x] Incorrect "Default" state
  - "WAITING" state should be considered "The tool recognizes the current screen/minigame and is waitin for user to activate"
  - "INACTIVE" state should be considered as "The tool does not recognize the current screen/minigame, therefore there is no automation available on this screen"
- [x] Overlay not anchored correctly
  - Top-right of overlay needs to be anchored to the top-right of WidgetInc.exe (reference .old.referenc-only/src/overlay_gui.py if needed)
  - Top-right of status indicator needs to be anchored to the top-right of the overlay
- [x] Overlay hover not working correctly
  - ~~Upon hover, the default overlay (32x32) jumps instantly left to, presumably, where the expanded top-left point is (this is why i know it's not anchored to the correct spot)~~ **FIXED: Animation now anchors from top-right**
  - ~~Hover actuation is instant, and does not wait the desired amount of time judging by the debug output below~~
  - ~~Hover actuation should be 0.25s, maybe even 0.5s~~ **CONFIRMED: Currently set to 0.5s (500ms)**

```
2025-07-14 00:18:34,602 - overlay.overlay_window - DEBUG - Mouse entered overlay
2025-07-14 00:18:34,616 - overlay.overlay_window - DEBUG - Mouse left overlay
2025-07-14 00:18:34,623 - overlay.overlay_window - DEBUG - Mouse entered overlay
2025-07-14 00:18:34,723 - overlay.overlay_window - DEBUG - Mouse left overlay
2025-07-14 00:18:34,911 - overlay.overlay_window - DEBUG - Mouse entered overlay
2025-07-14 00:18:35,169 - overlay.overlay_window - DEBUG - Expanding overlay
2025-07-14 00:18:35,190 - overlay.overlay_window - DEBUG - Mouse left overlay
```

- [x] Expanded overlay not displaying correctly

  - expanded overlay is not shaded (only the original 32x32 shaded box is present)
  - expanded overlay is missing colored status text in all caps
  - status indicator not anchored to the top-right of the expanded overlay

- [x] Overlay showing over all windows (always on top). Try granular z-indexing
  - **Reverted to always-on-top for now** - z-indexing can be addressed in future phase
