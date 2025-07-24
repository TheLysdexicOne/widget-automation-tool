"""
Widget Automation Tool - Main GUI Window

Comprehensive workbench environment for data collection and automation design.
Incorporates frame management, screenshot management, and region management.

Following project standards: KISS, DRY, industrialesque design.
"""

import logging
from pathlib import Path
from PyQt6.QtWidgets import (
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QTabWidget,
    QStatusBar,
    QToolBar,
    QSplitter,
    QTreeWidget,
    QTreeWidgetItem,
    QTableWidget,
    QTextEdit,
    QLabel,
    QPushButton,
    QGroupBox,
    QFormLayout,
    QComboBox,
    QSpinBox,
    QCheckBox,
    QProgressBar,
    QFileDialog,
    QMessageBox,
    QListWidget,
    QApplication,
)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QThread, QObject
from PyQt6.QtGui import QAction, QPixmap, QFont

from utility.database_manager import DatabaseManager
from utility.status_manager import StatusManager
from utility.window_utils import find_target_window


class DataCollectionWorker(QObject):
    """Background worker for data collection operations."""

    progress = pyqtSignal(int)
    finished = pyqtSignal(str)
    error = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self.is_running = False

    def start_collection(self):
        """Start data collection process."""
        self.is_running = True
        # Placeholder for actual data collection logic
        for i in range(101):
            if not self.is_running:
                break
            self.progress.emit(i)
            QThread.msleep(50)  # Simulate work
        self.finished.emit("Data collection completed")

    def stop_collection(self):
        """Stop data collection process."""
        self.is_running = False


class MainWindow(QMainWindow):
    """
    Main GUI window with comprehensive workbench environment.

    Features:
    - Frame Management integrated workbench
    - Screenshot Management with preview
    - Region Management with visual tools
    - Standard menu bar and status bar
    - Industrial dark theme styling
    """

    def __init__(self):
        super().__init__()
        self.logger = logging.getLogger(__name__)

        # Initialize data managers
        self.base_path = Path(__file__).parents[2]  # Project root
        self.database_manager = DatabaseManager(self.base_path)
        self.status_manager = StatusManager()

        # Initialize UI state
        self.current_frame = None
        self.selected_screenshots = []
        self.is_collecting_data = False

        # Background worker for data collection
        self.data_worker = None
        self.data_thread = None

        self._setup_window()
        self._setup_menu_bar()
        self._setup_toolbar()
        self._setup_central_widget()
        self._setup_status_bar()
        self._setup_timers()

        self.logger.info("MainWindow initialized")

    def _setup_window(self):
        """Setup main window properties."""
        self.setWindowTitle("Widget Automation Tool - Data Collection Workbench")
        self.setGeometry(100, 100, 1400, 900)
        self.setMinimumSize(1200, 700)

    def _setup_menu_bar(self):
        """Setup standard menu bar with File, Edit, View, Tools, Help."""
        # Ensure menubar exists
        try:
            menubar = self.menuBar()
            if menubar is None:
                return  # Skip menu setup if menubar creation failed
        except Exception as e:
            self.logger.warning(f"Failed to create menu bar: {e}")
            return

        # File Menu
        try:
            file_menu = menubar.addMenu("&File")
            if file_menu is not None:
                # Remove New Frame action as requested - start with Open Database
                open_action = QAction("&Open Database", self)
                open_action.setShortcut("Ctrl+O")
                open_action.triggered.connect(self._open_database)
                file_menu.addAction(open_action)

                save_action = QAction("&Save", self)
                save_action.setShortcut("Ctrl+S")
                save_action.triggered.connect(self._save_current)
                file_menu.addAction(save_action)

                file_menu.addSeparator()

                export_action = QAction("&Export Data", self)
                export_action.triggered.connect(self._export_data)
                file_menu.addAction(export_action)

                import_action = QAction("&Import Data", self)
                import_action.triggered.connect(self._import_data)
                file_menu.addAction(import_action)

                file_menu.addSeparator()

                # Exit action should exit the application completely, not just close window
                exit_action = QAction("E&xit", self)
                exit_action.setShortcut("Ctrl+Q")
                exit_action.triggered.connect(self._exit_application)
                file_menu.addAction(exit_action)
        except Exception as e:
            self.logger.warning(f"Failed to create file menu: {e}")

        # Edit Menu
        try:
            edit_menu = menubar.addMenu("&Edit")
            if edit_menu is not None:
                undo_action = QAction("&Undo", self)
                undo_action.setShortcut("Ctrl+Z")
                undo_action.setEnabled(False)  # Placeholder
                edit_menu.addAction(undo_action)

                redo_action = QAction("&Redo", self)
                redo_action.setShortcut("Ctrl+Y")
                redo_action.setEnabled(False)  # Placeholder
                edit_menu.addAction(redo_action)

                edit_menu.addSeparator()

                preferences_action = QAction("&Preferences", self)
                preferences_action.triggered.connect(self._show_preferences)
                edit_menu.addAction(preferences_action)
        except Exception as e:
            self.logger.warning(f"Failed to create edit menu: {e}")

        # View Menu
        try:
            view_menu = menubar.addMenu("&View")
            if view_menu is not None:
                refresh_action = QAction("&Refresh", self)
                refresh_action.setShortcut("F5")
                refresh_action.triggered.connect(self._refresh_data)
                view_menu.addAction(refresh_action)

                view_menu.addSeparator()

                zoom_in_action = QAction("Zoom &In", self)
                zoom_in_action.setShortcut("Ctrl++")
                zoom_in_action.triggered.connect(self._zoom_in)
                view_menu.addAction(zoom_in_action)

                zoom_out_action = QAction("Zoom &Out", self)
                zoom_out_action.setShortcut("Ctrl+-")
                zoom_out_action.triggered.connect(self._zoom_out)
                view_menu.addAction(zoom_out_action)
        except Exception as e:
            self.logger.warning(f"Failed to create view menu: {e}")

        # Tools Menu
        try:
            tools_menu = menubar.addMenu("&Tools")
            if tools_menu is not None:
                capture_action = QAction("&Capture Screenshot", self)
                capture_action.setShortcut("Ctrl+Shift+S")
                capture_action.triggered.connect(self._capture_screenshot)
                tools_menu.addAction(capture_action)

                analyze_action = QAction("&Analyze Frame", self)
                analyze_action.setShortcut("Ctrl+A")
                analyze_action.triggered.connect(self._analyze_frame)
                tools_menu.addAction(analyze_action)

                tools_menu.addSeparator()

                batch_action = QAction("&Batch Processing", self)
                batch_action.triggered.connect(self._batch_processing)
                tools_menu.addAction(batch_action)
        except Exception as e:
            self.logger.warning(f"Failed to create tools menu: {e}")

        # Help Menu
        try:
            help_menu = menubar.addMenu("&Help")
            if help_menu is not None:
                about_action = QAction("&About", self)
                about_action.triggered.connect(self._show_about)
                help_menu.addAction(about_action)

                help_action = QAction("&Help", self)
                help_action.setShortcut("F1")
                help_action.triggered.connect(self._show_help)
                help_menu.addAction(help_action)
        except Exception as e:
            self.logger.warning(f"Failed to create help menu: {e}")

    def _setup_toolbar(self):
        """Setup main toolbar with common actions."""
        toolbar = QToolBar("Main Toolbar")
        self.addToolBar(toolbar)

        # Quick action buttons
        new_btn = QPushButton("New Frame")
        new_btn.clicked.connect(self._new_frame)
        toolbar.addWidget(new_btn)

        toolbar.addSeparator()

        capture_btn = QPushButton("Capture")
        capture_btn.clicked.connect(self._capture_screenshot)
        toolbar.addWidget(capture_btn)

        analyze_btn = QPushButton("Analyze")
        analyze_btn.clicked.connect(self._analyze_frame)
        toolbar.addWidget(analyze_btn)

        toolbar.addSeparator()

        refresh_btn = QPushButton("Refresh")
        refresh_btn.clicked.connect(self._refresh_data)
        toolbar.addWidget(refresh_btn)

    def _setup_central_widget(self):
        """Setup the main workbench area with tabbed interface."""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        layout = QHBoxLayout(central_widget)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(4)

        # Create main splitter
        main_splitter = QSplitter(Qt.Orientation.Horizontal)
        layout.addWidget(main_splitter)

        # Left panel - Frame Explorer
        self._setup_frame_explorer(main_splitter)

        # Center panel - Main Workbench
        self._setup_workbench_tabs(main_splitter)

        # Right panel - Properties and Tools
        self._setup_properties_panel(main_splitter)

        # Set splitter proportions
        main_splitter.setSizes([250, 800, 350])

    def _setup_frame_explorer(self, parent):
        """Setup the frame explorer panel."""
        frame_panel = QWidget()
        frame_layout = QVBoxLayout(frame_panel)
        frame_layout.setContentsMargins(4, 4, 4, 4)

        # Frame Explorer Header
        header_label = QLabel("Frame Explorer")
        header_label.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
        frame_layout.addWidget(header_label)

        # Frame Tree
        self.frame_tree = QTreeWidget()
        self.frame_tree.setHeaderLabel("Frames Database")
        self.frame_tree.itemSelectionChanged.connect(self._on_frame_selected)
        frame_layout.addWidget(self.frame_tree)

        # Frame actions
        frame_actions = QHBoxLayout()

        add_frame_btn = QPushButton("Add")
        add_frame_btn.clicked.connect(self._new_frame)
        frame_actions.addWidget(add_frame_btn)

        edit_frame_btn = QPushButton("Edit")
        edit_frame_btn.clicked.connect(self._edit_frame)
        frame_actions.addWidget(edit_frame_btn)

        delete_frame_btn = QPushButton("Delete")
        delete_frame_btn.clicked.connect(self._delete_frame)
        frame_actions.addWidget(delete_frame_btn)

        frame_layout.addLayout(frame_actions)

        parent.addWidget(frame_panel)

    def _setup_workbench_tabs(self, parent):
        """Setup the main workbench tabbed interface."""
        self.workbench_tabs = QTabWidget()

        # Frame Management Tab
        self._setup_frame_management_tab()

        # Screenshot Management Tab
        self._setup_screenshot_management_tab()

        # Region Management Tab
        self._setup_region_management_tab()

        # Data Collection Tab
        self._setup_data_collection_tab()

        parent.addWidget(self.workbench_tabs)

    def _setup_frame_management_tab(self):
        """Setup the frame management workbench tab."""
        frame_tab = QWidget()
        layout = QVBoxLayout(frame_tab)

        # Frame details form
        details_group = QGroupBox("Frame Details")
        details_layout = QFormLayout(details_group)

        self.frame_id_edit = QComboBox()
        self.frame_id_edit.setEditable(True)
        details_layout.addRow("Frame ID:", self.frame_id_edit)

        self.frame_name_edit = QComboBox()
        self.frame_name_edit.setEditable(True)
        details_layout.addRow("Frame Name:", self.frame_name_edit)

        self.frame_item_edit = QComboBox()
        self.frame_item_edit.setEditable(True)
        details_layout.addRow("Item Type:", self.frame_item_edit)

        self.automation_enabled = QCheckBox("Automation Enabled")
        details_layout.addRow("Settings:", self.automation_enabled)

        layout.addWidget(details_group)

        # Frame statistics
        stats_group = QGroupBox("Frame Statistics")
        stats_layout = QFormLayout(stats_group)

        self.screenshot_count_label = QLabel("0")
        stats_layout.addRow("Screenshots:", self.screenshot_count_label)

        self.text_regions_label = QLabel("0")
        stats_layout.addRow("Text Regions:", self.text_regions_label)

        self.interact_regions_label = QLabel("0")
        stats_layout.addRow("Interact Regions:", self.interact_regions_label)

        layout.addWidget(stats_group)

        # Actions
        actions_layout = QHBoxLayout()

        save_frame_btn = QPushButton("Save Frame")
        save_frame_btn.clicked.connect(self._save_current)
        actions_layout.addWidget(save_frame_btn)

        duplicate_frame_btn = QPushButton("Duplicate")
        duplicate_frame_btn.clicked.connect(self._duplicate_frame)
        actions_layout.addWidget(duplicate_frame_btn)

        layout.addLayout(actions_layout)
        layout.addStretch()

        self.workbench_tabs.addTab(frame_tab, "Frame Management")

    def _setup_screenshot_management_tab(self):
        """Setup the screenshot management workbench tab."""
        screenshot_tab = QWidget()
        layout = QVBoxLayout(screenshot_tab)

        # Screenshot list and preview
        screenshot_splitter = QSplitter(Qt.Orientation.Horizontal)

        # Screenshot list
        list_widget = QWidget()
        list_layout = QVBoxLayout(list_widget)

        list_header = QLabel("Screenshots")
        list_header.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
        list_layout.addWidget(list_header)

        self.screenshot_list = QListWidget()
        self.screenshot_list.itemSelectionChanged.connect(self._on_screenshot_selected)
        list_layout.addWidget(self.screenshot_list)

        # Screenshot actions
        screenshot_actions = QHBoxLayout()

        add_screenshot_btn = QPushButton("Add")
        add_screenshot_btn.clicked.connect(self._add_screenshot)
        screenshot_actions.addWidget(add_screenshot_btn)

        remove_screenshot_btn = QPushButton("Remove")
        remove_screenshot_btn.clicked.connect(self._remove_screenshot)
        screenshot_actions.addWidget(remove_screenshot_btn)

        set_primary_btn = QPushButton("Set Primary")
        set_primary_btn.clicked.connect(self._set_primary_screenshot)
        screenshot_actions.addWidget(set_primary_btn)

        list_layout.addLayout(screenshot_actions)

        screenshot_splitter.addWidget(list_widget)

        # Screenshot preview
        preview_widget = QWidget()
        preview_layout = QVBoxLayout(preview_widget)

        preview_header = QLabel("Preview")
        preview_header.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
        preview_layout.addWidget(preview_header)

        self.screenshot_preview = QLabel("No screenshot selected")
        self.screenshot_preview.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.screenshot_preview.setStyleSheet("border: 1px solid #555; background-color: #1e1e1e;")
        self.screenshot_preview.setMinimumSize(400, 300)
        preview_layout.addWidget(self.screenshot_preview)

        screenshot_splitter.addWidget(preview_widget)
        screenshot_splitter.setSizes([300, 500])

        layout.addWidget(screenshot_splitter)

        self.workbench_tabs.addTab(screenshot_tab, "Screenshot Management")

    def _setup_region_management_tab(self):
        """Setup the region management workbench tab."""
        region_tab = QWidget()
        layout = QVBoxLayout(region_tab)

        # Region tools
        tools_group = QGroupBox("Region Tools")
        tools_layout = QHBoxLayout(tools_group)

        text_region_btn = QPushButton("Add Text Region")
        text_region_btn.clicked.connect(self._add_text_region)
        tools_layout.addWidget(text_region_btn)

        interact_region_btn = QPushButton("Add Interact Region")
        interact_region_btn.clicked.connect(self._add_interact_region)
        tools_layout.addWidget(interact_region_btn)

        delete_region_btn = QPushButton("Delete Region")
        delete_region_btn.clicked.connect(self._delete_region)
        tools_layout.addWidget(delete_region_btn)

        layout.addWidget(tools_group)

        # Region list
        regions_group = QGroupBox("Regions")
        regions_layout = QVBoxLayout(regions_group)

        self.regions_table = QTableWidget()
        self.regions_table.setColumnCount(4)
        self.regions_table.setHorizontalHeaderLabels(["Type", "Name", "Position", "Size"])
        regions_layout.addWidget(self.regions_table)

        layout.addWidget(regions_group)

        # Region properties
        props_group = QGroupBox("Region Properties")
        props_layout = QFormLayout(props_group)

        self.region_name_edit = QComboBox()
        self.region_name_edit.setEditable(True)
        props_layout.addRow("Name:", self.region_name_edit)

        self.region_x_spin = QSpinBox()
        self.region_x_spin.setRange(0, 9999)
        props_layout.addRow("X Position:", self.region_x_spin)

        self.region_y_spin = QSpinBox()
        self.region_y_spin.setRange(0, 9999)
        props_layout.addRow("Y Position:", self.region_y_spin)

        self.region_width_spin = QSpinBox()
        self.region_width_spin.setRange(1, 9999)
        props_layout.addRow("Width:", self.region_width_spin)

        self.region_height_spin = QSpinBox()
        self.region_height_spin.setRange(1, 9999)
        props_layout.addRow("Height:", self.region_height_spin)

        layout.addWidget(props_group)

        self.workbench_tabs.addTab(region_tab, "Region Management")

    def _setup_data_collection_tab(self):
        """Setup the data collection and analysis tab."""
        data_tab = QWidget()
        layout = QVBoxLayout(data_tab)

        # Data collection controls
        collection_group = QGroupBox("Data Collection")
        collection_layout = QVBoxLayout(collection_group)

        control_layout = QHBoxLayout()

        self.start_collection_btn = QPushButton("Start Collection")
        self.start_collection_btn.clicked.connect(self._start_data_collection)
        control_layout.addWidget(self.start_collection_btn)

        self.stop_collection_btn = QPushButton("Stop Collection")
        self.stop_collection_btn.clicked.connect(self._stop_data_collection)
        self.stop_collection_btn.setEnabled(False)
        control_layout.addWidget(self.stop_collection_btn)

        control_layout.addStretch()

        collection_layout.addLayout(control_layout)

        # Progress bar
        self.collection_progress = QProgressBar()
        collection_layout.addWidget(self.collection_progress)

        # Collection log
        self.collection_log = QTextEdit()
        self.collection_log.setMaximumHeight(200)
        self.collection_log.setReadOnly(True)
        collection_layout.addWidget(self.collection_log)

        layout.addWidget(collection_group)

        # Analysis results
        analysis_group = QGroupBox("Analysis Results")
        analysis_layout = QVBoxLayout(analysis_group)

        self.analysis_results = QTextEdit()
        self.analysis_results.setReadOnly(True)
        analysis_layout.addWidget(self.analysis_results)

        layout.addWidget(analysis_group)

        self.workbench_tabs.addTab(data_tab, "Data Collection")

    def _setup_properties_panel(self, parent):
        """Setup the properties and tools panel."""
        properties_panel = QWidget()
        properties_layout = QVBoxLayout(properties_panel)
        properties_layout.setContentsMargins(4, 4, 4, 4)

        # Target Window Status
        target_group = QGroupBox("Target Window")
        target_layout = QFormLayout(target_group)

        self.target_status_label = QLabel("Not Connected")
        target_layout.addRow("Status:", self.target_status_label)

        self.target_process_label = QLabel("N/A")
        target_layout.addRow("Process:", self.target_process_label)

        self.target_window_label = QLabel("N/A")
        target_layout.addRow("Window:", self.target_window_label)

        connect_btn = QPushButton("Connect to Target")
        connect_btn.clicked.connect(self._connect_to_target)
        target_layout.addRow(connect_btn)

        properties_layout.addWidget(target_group)

        # Quick Tools
        tools_group = QGroupBox("Quick Tools")
        tools_layout = QVBoxLayout(tools_group)

        window_spy_btn = QPushButton("Window Spy")
        window_spy_btn.clicked.connect(self._open_window_spy)
        tools_layout.addWidget(window_spy_btn)

        color_picker_btn = QPushButton("Color Picker")
        color_picker_btn.clicked.connect(self._open_color_picker)
        tools_layout.addWidget(color_picker_btn)

        coordinate_tracker_btn = QPushButton("Coordinate Tracker")
        coordinate_tracker_btn.clicked.connect(self._open_coordinate_tracker)
        tools_layout.addWidget(coordinate_tracker_btn)

        properties_layout.addWidget(tools_group)

        # Recent Activity
        activity_group = QGroupBox("Recent Activity")
        activity_layout = QVBoxLayout(activity_group)

        self.activity_log = QTextEdit()
        self.activity_log.setMaximumHeight(150)
        self.activity_log.setReadOnly(True)
        activity_layout.addWidget(self.activity_log)

        properties_layout.addWidget(activity_group)

        properties_layout.addStretch()

        parent.addWidget(properties_panel)

    def _setup_status_bar(self):
        """Setup the bottom status bar."""
        status_bar = QStatusBar()
        self.setStatusBar(status_bar)

        # Status message
        self.status_message = QLabel("Ready")
        status_bar.addWidget(self.status_message)

        # Progress indicator
        self.status_progress = QProgressBar()
        self.status_progress.setVisible(False)
        self.status_progress.setMaximumWidth(200)
        status_bar.addPermanentWidget(self.status_progress)

        # Connection status
        self.connection_status = QLabel("Disconnected")
        self.connection_status.setStyleSheet("color: #ff6b6b;")
        status_bar.addPermanentWidget(self.connection_status)

        # Frame count
        self.frame_count_status = QLabel("Frames: 0")
        status_bar.addPermanentWidget(self.frame_count_status)

    def _setup_timers(self):
        """Setup timers for periodic updates."""
        # Target window monitoring
        self.target_timer = QTimer()
        self.target_timer.timeout.connect(self._check_target_window)
        self.target_timer.start(2000)  # Check every 2 seconds

        # Data refresh timer
        self.refresh_timer = QTimer()
        self.refresh_timer.timeout.connect(self._periodic_refresh)
        self.refresh_timer.start(10000)  # Refresh every 10 seconds

    def setWindowIcon(self, icon):
        """Override to set taskbar icon properly."""
        super().setWindowIcon(icon)
        # Additional Windows-specific taskbar icon handling if needed
        # The super() call should handle the actual icon setting

    # --- Event Handlers ---

    def _on_frame_selected(self):
        """Handle frame selection in the explorer."""
        selected_items = self.frame_tree.selectedItems()
        if selected_items:
            item = selected_items[0]
            frame_data = item.data(0, Qt.ItemDataRole.UserRole)
            if frame_data:
                self.current_frame = frame_data
                self._update_frame_details()
                self._log_activity(f"Selected frame: {frame_data.get('name', 'Unknown')}")

    def _on_screenshot_selected(self):
        """Handle screenshot selection."""
        current_item = self.screenshot_list.currentItem()
        if current_item:
            screenshot_path = current_item.data(Qt.ItemDataRole.UserRole)
            self._load_screenshot_preview(screenshot_path)

    # --- Menu Actions ---

    def _new_frame(self):
        """Create a new frame."""
        self._log_activity("Creating new frame")
        self.status_message.setText("Creating new frame...")
        # Implementation placeholder

    def _open_database(self):
        """Open database file."""
        file_path, _ = QFileDialog.getOpenFileName(self, "Open Database", "", "JSON Files (*.json);;All Files (*)")
        if file_path:
            self._log_activity(f"Opening database: {file_path}")

    def _save_current(self):
        """Save current frame."""
        if self.current_frame:
            self._log_activity(f"Saving frame: {self.current_frame.get('name', 'Unknown')}")
            self.status_message.setText("Frame saved")

    def _export_data(self):
        """Export data to file."""
        file_path, _ = QFileDialog.getSaveFileName(self, "Export Data", "", "JSON Files (*.json);;All Files (*)")
        if file_path:
            self._log_activity(f"Exporting data to: {file_path}")

    def _import_data(self):
        """Import data from file."""
        file_path, _ = QFileDialog.getOpenFileName(self, "Import Data", "", "JSON Files (*.json);;All Files (*)")
        if file_path:
            self._log_activity(f"Importing data from: {file_path}")

    def _show_preferences(self):
        """Show preferences dialog."""
        self._log_activity("Opening preferences")

    def _refresh_data(self):
        """Refresh all data."""
        self._log_activity("Refreshing data")
        self._load_frames()
        self.status_message.setText("Data refreshed")

    def _zoom_in(self):
        """Zoom in the current view."""
        self._log_activity("Zooming in")

    def _zoom_out(self):
        """Zoom out the current view."""
        self._log_activity("Zooming out")

    def _capture_screenshot(self):
        """Capture screenshot of target window."""
        self._log_activity("Capturing screenshot")
        self.status_message.setText("Capturing screenshot...")

    def _analyze_frame(self):
        """Analyze current frame."""
        if self.current_frame:
            self._log_activity(f"Analyzing frame: {self.current_frame.get('name', 'Unknown')}")
            self.status_message.setText("Analyzing frame...")

    def _batch_processing(self):
        """Open batch processing dialog."""
        self._log_activity("Opening batch processing")

    def _show_about(self):
        """Show about dialog."""
        QMessageBox.about(
            self,
            "About Widget Automation Tool",
            "Widget Automation Tool v2.0.0\n\n"
            "Industrial automation workbench for data collection and automation design.\n\n"
            "Following KISS and DRY principles with industrialesque design.",
        )

    def _show_help(self):
        """Show help dialog."""
        self._log_activity("Opening help")

    # --- Workbench Actions ---

    def _edit_frame(self):
        """Edit selected frame."""
        if self.current_frame:
            self._log_activity(f"Editing frame: {self.current_frame.get('name', 'Unknown')}")

    def _delete_frame(self):
        """Delete selected frame."""
        if self.current_frame:
            reply = QMessageBox.question(
                self,
                "Delete Frame",
                f"Are you sure you want to delete frame '{self.current_frame.get('name', 'Unknown')}'?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            )
            if reply == QMessageBox.StandardButton.Yes:
                self._log_activity(f"Deleting frame: {self.current_frame.get('name', 'Unknown')}")

    def _duplicate_frame(self):
        """Duplicate current frame."""
        if self.current_frame:
            self._log_activity(f"Duplicating frame: {self.current_frame.get('name', 'Unknown')}")

    def _add_screenshot(self):
        """Add screenshot to current frame."""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Add Screenshot", "", "Image Files (*.png *.jpg *.jpeg *.bmp);;All Files (*)"
        )
        if file_path:
            self._log_activity(f"Adding screenshot: {file_path}")

    def _remove_screenshot(self):
        """Remove selected screenshot."""
        current_item = self.screenshot_list.currentItem()
        if current_item:
            self._log_activity("Removing screenshot")

    def _set_primary_screenshot(self):
        """Set selected screenshot as primary."""
        current_item = self.screenshot_list.currentItem()
        if current_item:
            self._log_activity("Setting primary screenshot")

    def _add_text_region(self):
        """Add text region to current frame."""
        self._log_activity("Adding text region")

    def _add_interact_region(self):
        """Add interact region to current frame."""
        self._log_activity("Adding interact region")

    def _delete_region(self):
        """Delete selected region."""
        self._log_activity("Deleting region")

    def _start_data_collection(self):
        """Start data collection process."""
        if not self.is_collecting_data:
            self.is_collecting_data = True
            self.start_collection_btn.setEnabled(False)
            self.stop_collection_btn.setEnabled(True)
            self.status_progress.setVisible(True)

            # Start background worker
            self.data_thread = QThread()
            self.data_worker = DataCollectionWorker()
            self.data_worker.moveToThread(self.data_thread)

            self.data_worker.progress.connect(self.collection_progress.setValue)
            self.data_worker.progress.connect(self.status_progress.setValue)
            self.data_worker.finished.connect(self._data_collection_finished)
            self.data_worker.error.connect(self._data_collection_error)

            self.data_thread.started.connect(self.data_worker.start_collection)
            self.data_thread.start()

            self._log_activity("Started data collection")

    def _stop_data_collection(self):
        """Stop data collection process."""
        if self.is_collecting_data and self.data_worker:
            self.data_worker.stop_collection()
            self._log_activity("Stopping data collection")

    def _data_collection_finished(self, message):
        """Handle data collection completion."""
        self.is_collecting_data = False
        self.start_collection_btn.setEnabled(True)
        self.stop_collection_btn.setEnabled(False)
        self.status_progress.setVisible(False)

        if self.data_thread:
            self.data_thread.quit()
            self.data_thread.wait()

        self._log_activity(f"Data collection finished: {message}")
        self.collection_log.append(f"[FINISHED] {message}")

    def _data_collection_error(self, error):
        """Handle data collection error."""
        self.is_collecting_data = False
        self.start_collection_btn.setEnabled(True)
        self.stop_collection_btn.setEnabled(False)
        self.status_progress.setVisible(False)

        self._log_activity(f"Data collection error: {error}")
        self.collection_log.append(f"[ERROR] {error}")

    def _connect_to_target(self):
        """Connect to target window."""
        target_info = find_target_window("WidgetInc.exe")
        if target_info:
            self.target_status_label.setText("Connected")
            self.target_status_label.setStyleSheet("color: #51cf66;")
            self.connection_status.setText("Connected")
            self.connection_status.setStyleSheet("color: #51cf66;")
            self._log_activity("Connected to target window")
        else:
            self.target_status_label.setText("Not Found")
            self.target_status_label.setStyleSheet("color: #ff6b6b;")
            self._log_activity("Target window not found")

    def _open_window_spy(self):
        """Open window spy tool."""
        self._log_activity("Opening window spy")

    def _open_color_picker(self):
        """Open color picker tool."""
        self._log_activity("Opening color picker")

    def _open_coordinate_tracker(self):
        """Open coordinate tracker tool."""
        self._log_activity("Opening coordinate tracker")

    # --- Helper Methods ---

    def _load_frames(self):
        """Load frames from database."""
        try:
            frames = self.database_manager.get_frame_list()
            self.frame_tree.clear()

            for frame in frames:
                item = QTreeWidgetItem(self.frame_tree)
                item.setText(0, f"{frame.get('id', '?')}: {frame.get('name', 'Unknown')}")
                item.setData(0, Qt.ItemDataRole.UserRole, frame)

            self.frame_count_status.setText(f"Frames: {len(frames)}")
            self._log_activity(f"Loaded {len(frames)} frames")

        except Exception as e:
            self.logger.error(f"Error loading frames: {e}")
            self._log_activity(f"Error loading frames: {e}")

    def _update_frame_details(self):
        """Update frame details in the UI."""
        if self.current_frame:
            self.frame_id_edit.setCurrentText(self.current_frame.get("id", ""))
            self.frame_name_edit.setCurrentText(self.current_frame.get("name", ""))
            self.frame_item_edit.setCurrentText(self.current_frame.get("item", ""))
            self.automation_enabled.setChecked(self.current_frame.get("automation", 0) == 1)

            # Update statistics
            screenshots = self.current_frame.get("screenshots", [])
            self.screenshot_count_label.setText(str(len(screenshots)))

            regions = self.current_frame.get("regions", {})
            text_regions = regions.get("text", [])
            interact_regions = regions.get("interact", [])
            self.text_regions_label.setText(str(len(text_regions)))
            self.interact_regions_label.setText(str(len(interact_regions)))

    def _load_screenshot_preview(self, screenshot_path):
        """Load screenshot preview."""
        if screenshot_path and Path(screenshot_path).exists():
            pixmap = QPixmap(screenshot_path)
            if not pixmap.isNull():
                # Scale to fit preview area
                scaled_pixmap = pixmap.scaled(
                    self.screenshot_preview.size(),
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation,
                )
                self.screenshot_preview.setPixmap(scaled_pixmap)
            else:
                self.screenshot_preview.setText("Invalid image file")
        else:
            self.screenshot_preview.setText("Image file not found")

    def _check_target_window(self):
        """Periodically check target window status."""
        target_info = find_target_window("WidgetInc.exe")
        if target_info:
            if self.target_status_label.text() != "Connected":
                self.target_status_label.setText("Connected")
                self.target_status_label.setStyleSheet("color: #51cf66;")
                self.connection_status.setText("Connected")
                self.connection_status.setStyleSheet("color: #51cf66;")
        else:
            if self.target_status_label.text() != "Not Found":
                self.target_status_label.setText("Not Found")
                self.target_status_label.setStyleSheet("color: #ff6b6b;")
                self.connection_status.setText("Disconnected")
                self.connection_status.setStyleSheet("color: #ff6b6b;")

    def _periodic_refresh(self):
        """Periodic data refresh."""
        if not self.is_collecting_data:
            # Light refresh without UI disruption
            try:
                frames = self.database_manager.get_frame_list()
                current_count = self.frame_tree.topLevelItemCount()
                if len(frames) != current_count:
                    self._load_frames()
            except Exception as e:
                self.logger.debug(f"Periodic refresh error: {e}")

    def _log_activity(self, message):
        """Log activity to the activity log."""
        from datetime import datetime

        timestamp = datetime.now().strftime("%H:%M:%S")
        formatted_message = f"[{timestamp}] {message}"
        self.activity_log.append(formatted_message)

        # Keep only last 100 lines
        document = self.activity_log.document()
        if document and document.lineCount() > 100:
            cursor = self.activity_log.textCursor()
            cursor.movePosition(cursor.MoveOperation.Start)
            cursor.select(cursor.SelectionType.LineUnderCursor)
            cursor.removeSelectedText()

    def showEvent(self, event):
        """Handle window show event."""
        super().showEvent(event)
        # Load initial data when window is first shown
        if not hasattr(self, "_initial_load_done"):
            self._load_frames()
            self._initial_load_done = True
            self._log_activity("MainWindow initialized and data loaded")

    def closeEvent(self, event):
        """Handle window close event - minimize to tray instead of closing."""
        # Instead of closing completely, just minimize/hide the window
        # This keeps the application running in the background
        self._log_activity("MainWindow minimizing to tray")
        event.ignore()  # Don't actually close the window
        self.hide()  # Just hide it instead

    def _exit_application(self):
        """Exit the application completely, not just close window."""
        self._log_activity("Application exit requested")

        # Perform cleanup
        if self.is_collecting_data:
            self._stop_data_collection()

        # Stop timers
        if hasattr(self, "target_timer"):
            self.target_timer.stop()
        if hasattr(self, "refresh_timer"):
            self.refresh_timer.stop()

        # Exit the application
        QApplication.quit()
