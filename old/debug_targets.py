#!/usr/bin/env python3
"""
Quick verification script to show available processes and windows
"""

import psutil
import pygetwindow as gw

print("=== Available Processes ===")
for process in psutil.process_iter(["pid", "name"]):
    try:
        if any(
            name in process.info["name"].lower()
            for name in ["notepad", "calc", "widget"]
        ):
            print(f"PID: {process.info['pid']}, Name: {process.info['name']}")
    except (psutil.NoSuchProcess, psutil.AccessDenied):
        continue

print("\n=== Available Windows ===")
all_windows = gw.getAllWindows()
for window in all_windows:
    try:
        if window.visible and window.title and len(window.title.strip()) > 0:
            # Filter for interesting windows
            if any(
                name in window.title.lower()
                for name in ["notepad", "calculator", "widget", "untitled"]
            ):
                print(
                    f"Title: '{window.title}', HWND: {getattr(window, '_hWnd', 'N/A')}"
                )
    except Exception:
        continue

print("\n=== Testing Complete ===")
