"""
Debug tab for debug console - handles component testing and debugging.
"""

from PyQt6.QtWidgets import (
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QTreeWidget,
    QTreeWidgetItem,
)
from PyQt6.QtCore import QTimer

from .base_tab import BaseTab


class DebugTab(BaseTab):
    """Debug tab for component testing and debugging."""

    def _setup_ui(self):
        """Setup the debug tab UI."""
        layout = QVBoxLayout(self)

        # Component status
        self.component_tree = QTreeWidget()
        self.component_tree.setHeaderLabels(["Component", "Status", "Details"])
        layout.addWidget(QLabel("Component Status:"))
        layout.addWidget(self.component_tree)

        # Debug actions
        debug_actions_layout = QHBoxLayout()

        refresh_btn = QPushButton("Refresh")
        refresh_btn.clicked.connect(self._refresh_debug_info)
        debug_actions_layout.addWidget(refresh_btn)

        test_btn = QPushButton("Run Tests")
        test_btn.clicked.connect(self._run_debug_tests)
        debug_actions_layout.addWidget(test_btn)

        debug_actions_layout.addStretch()
        layout.addLayout(debug_actions_layout)

    def _refresh_debug_info(self):
        """Refresh the debug information."""
        try:
            # Clear the component tree
            self.component_tree.clear()

            # Create root items for each component
            components = {
                "Application": self.app,
                "System Tray": getattr(self.app, "system_tray", None),
                "Process Monitor": getattr(self.app, "process_monitor", None),
                "Overlay Window": getattr(self.app, "overlay_window", None),
                "Debug Console": self.parent(),
            }

            for component_name, component in components.items():
                item = QTreeWidgetItem(self.component_tree)
                item.setText(0, component_name)

                if component is None:
                    item.setText(1, "Not Available")
                    item.setText(2, "Component not initialized")
                else:
                    item.setText(1, "Available")

                    # Add specific details for each component
                    if component_name == "Application":
                        if hasattr(component, "get_state"):
                            state = component.get_state()
                            item.setText(2, f"State: {state.value.title()}")
                        else:
                            item.setText(2, "State management not available")

                    elif component_name == "System Tray":
                        if hasattr(component, "tray_icon") and component.tray_icon:
                            item.setText(1, "Active")
                            item.setText(2, "System tray icon visible")
                        else:
                            item.setText(1, "Inactive")
                            item.setText(2, "System tray icon not created")

                    elif component_name == "Process Monitor":
                        if hasattr(component, "is_monitoring"):
                            if component.is_monitoring:
                                item.setText(1, "Monitoring")
                                target_info = component.get_current_target_info()
                                if target_info:
                                    item.setText(
                                        2, f"Target found: PID {target_info['pid']}"
                                    )
                                else:
                                    item.setText(2, "Monitoring but target not found")
                            else:
                                item.setText(1, "Stopped")
                                item.setText(2, "Not monitoring")
                        else:
                            item.setText(2, "Monitor interface not available")

                    elif component_name == "Overlay Window":
                        if hasattr(component, "isVisible"):
                            if component.isVisible():
                                item.setText(1, "Visible")
                                geometry = component.geometry()
                                item.setText(
                                    2,
                                    f"Position: {geometry.x()},{geometry.y()} Size: {geometry.width()}x{geometry.height()}",
                                )
                            else:
                                item.setText(1, "Hidden")
                                item.setText(2, "Window created but not visible")
                        else:
                            item.setText(2, "Window interface not available")

                    elif component_name == "Debug Console":
                        item.setText(1, "Active")
                        if hasattr(component, "tab_widget"):
                            tab_count = component.tab_widget.count()
                            item.setText(2, f"Tabs: {tab_count}")
                        else:
                            item.setText(2, "Console active")

            # Expand all items
            self.component_tree.expandAll()

            # Notify parent if possible
            if hasattr(self.parent(), "statusBar"):
                self.parent().statusBar().showMessage(
                    "Debug information refreshed", 2000
                )

        except Exception as e:
            self.logger.error(f"Error refreshing debug info: {e}")
            if hasattr(self.parent(), "statusBar"):
                self.parent().statusBar().showMessage(
                    f"Error refreshing debug info: {e}", 5000
                )

    def _run_debug_tests(self):
        """Run debug tests to validate component functionality."""
        try:
            self.logger.info("Starting debug tests...")

            test_results = []

            # Test 1: Application state
            try:
                if hasattr(self.app, "get_state"):
                    state = self.app.get_state()
                    test_results.append(
                        ("Application State", "PASS", f"Current state: {state.value}")
                    )
                else:
                    test_results.append(
                        ("Application State", "FAIL", "No get_state method")
                    )
            except Exception as e:
                test_results.append(("Application State", "ERROR", str(e)))

            # Test 2: System Tray
            try:
                if hasattr(self.app, "system_tray") and self.app.system_tray:
                    if (
                        hasattr(self.app.system_tray, "tray_icon")
                        and self.app.system_tray.tray_icon
                    ):
                        test_results.append(("System Tray", "PASS", "Tray icon active"))
                    else:
                        test_results.append(
                            ("System Tray", "FAIL", "Tray icon not found")
                        )
                else:
                    test_results.append(
                        ("System Tray", "FAIL", "System tray not initialized")
                    )
            except Exception as e:
                test_results.append(("System Tray", "ERROR", str(e)))

            # Test 3: Process Monitor
            try:
                if hasattr(self.app, "process_monitor") and self.app.process_monitor:
                    if self.app.process_monitor.is_monitoring:
                        target_info = self.app.process_monitor.get_current_target_info()
                        if target_info:
                            test_results.append(
                                (
                                    "Process Monitor",
                                    "PASS",
                                    f"Target found: PID {target_info['pid']}",
                                )
                            )
                        else:
                            test_results.append(
                                (
                                    "Process Monitor",
                                    "WARNING",
                                    "Monitoring but no target found",
                                )
                            )
                    else:
                        test_results.append(
                            ("Process Monitor", "WARNING", "Not currently monitoring")
                        )
                else:
                    test_results.append(
                        ("Process Monitor", "FAIL", "Process monitor not initialized")
                    )
            except Exception as e:
                test_results.append(("Process Monitor", "ERROR", str(e)))

            # Test 4: Overlay Window
            try:
                if hasattr(self.app, "overlay_window") and self.app.overlay_window:
                    if self.app.overlay_window.isVisible():
                        test_results.append(
                            ("Overlay Window", "PASS", "Window visible")
                        )
                    else:
                        test_results.append(
                            ("Overlay Window", "WARNING", "Window hidden")
                        )
                else:
                    test_results.append(
                        ("Overlay Window", "FAIL", "Overlay window not initialized")
                    )
            except Exception as e:
                test_results.append(("Overlay Window", "ERROR", str(e)))

            # Test 5: Debug Console (self-test)
            try:
                parent_console = self.parent()
                if hasattr(parent_console, "tab_widget"):
                    tab_count = parent_console.tab_widget.count()
                    test_results.append(("Debug Console", "PASS", f"Tabs: {tab_count}"))
                else:
                    test_results.append(("Debug Console", "PASS", "Console active"))
            except Exception as e:
                test_results.append(("Debug Console", "ERROR", str(e)))

            # Log test results
            for test_name, result, details in test_results:
                if result == "PASS":
                    self.logger.info(f"TEST {test_name}: {result} - {details}")
                elif result == "WARNING":
                    self.logger.warning(f"TEST {test_name}: {result} - {details}")
                elif result == "FAIL":
                    self.logger.error(f"TEST {test_name}: {result} - {details}")
                elif result == "ERROR":
                    self.logger.error(f"TEST {test_name}: {result} - {details}")

            # Summary
            pass_count = sum(1 for _, result, _ in test_results if result == "PASS")
            total_count = len(test_results)

            self.logger.info(
                f"Debug tests completed: {pass_count}/{total_count} passed"
            )

            # Notify parent if possible
            if hasattr(self.parent(), "statusBar"):
                self.parent().statusBar().showMessage(
                    f"Debug tests completed: {pass_count}/{total_count} passed", 5000
                )

        except Exception as e:
            self.logger.error(f"Error running debug tests: {e}")
            if hasattr(self.parent(), "statusBar"):
                self.parent().statusBar().showMessage(
                    f"Error running debug tests: {e}", 5000
                )

    def on_tab_activated(self):
        """Called when debug tab becomes active."""
        # Refresh debug info when tab is activated
        QTimer.singleShot(100, self._refresh_debug_info)
