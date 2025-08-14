"""
Frame Border Analysis Tool - Standalone Border Analysis Application

This tool analyzes left and right borders of frames for unique identification patterns.
Operates independently of the main application while leveraging existing infrastructure.

Border Analysis Regions:
- Left Border: 5% inset from left edge, 20% center strip of frame height
- Right Border: 5% inset from right edge, 20% center strip of frame height

Following project standards: KISS, DRY, standalone operation.
"""

import sys
import os
import json
from pathlib import Path
from datetime import datetime

from PyQt6.QtWidgets import (
    QApplication,
    QMainWindow,
    QVBoxLayout,
    QHBoxLayout,
    QWidget,
    QComboBox,
    QPushButton,
    QLabel,
    QTextEdit,
    QProgressBar,
    QGroupBox,
    QMessageBox,
    QSplitter,
)
from PyQt6.QtCore import QThread, pyqtSignal, Qt
from PyQt6.QtGui import QFont, QIcon

# Add src to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from utility.cache_manager import get_cache_manager
from analyze.border_analysis_engine import BorderAnalysisEngine
from analyze.analysis_database import AnalysisDatabase


class AnalysisWorker(QThread):
    """Worker thread for border analysis to keep UI responsive"""

    progress = pyqtSignal(str)
    finished = pyqtSignal(dict)
    error = pyqtSignal(str)

    def __init__(self, frame_data, analysis_engine):
        super().__init__()
        self.frame_data = frame_data
        self.analysis_engine = analysis_engine

    def run(self):
        try:
            self.progress.emit(f"Analyzing frame: {self.frame_data['name']}")
            result = self.analysis_engine.analyze_frame_borders(self.frame_data)
            self.finished.emit(result)
        except Exception as e:
            self.error.emit(f"Analysis failed: {str(e)}")


class FrameAnalyzerWindow(QMainWindow):
    """Standalone frame border analysis tool"""

    def __init__(self):
        super().__init__()
        self.cache_manager = get_cache_manager()
        self.analysis_engine = BorderAnalysisEngine()
        self.analysis_db = AnalysisDatabase()
        self.worker = None

        self.setWindowTitle("Frame Border Analysis Tool")
        self.setGeometry(100, 100, 1000, 700)

        # Set window icon if available
        icon_path = Path(__file__).parent.parent.parent / "assets" / "icons" / "development-64.png"
        if icon_path.exists():
            self.setWindowIcon(QIcon(str(icon_path)))

        self.setup_ui()
        self.load_frames()
        self.check_window_availability()

    def setup_ui(self):
        """Setup the UI components"""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # Create main splitter for layout
        main_splitter = QSplitter(Qt.Orientation.Vertical)
        central_widget_layout = QVBoxLayout(central_widget)
        central_widget_layout.addWidget(main_splitter)

        # Top section for controls
        controls_widget = QWidget()
        controls_layout = QVBoxLayout(controls_widget)

        # Frame selection group
        frame_group = QGroupBox("Frame Selection")
        frame_layout = QHBoxLayout(frame_group)

        self.frame_combo = QComboBox()
        self.frame_combo.setMinimumWidth(300)
        frame_layout.addWidget(QLabel("Select Frame:"))
        frame_layout.addWidget(self.frame_combo)
        frame_layout.addStretch()

        controls_layout.addWidget(frame_group)

        # Analysis controls group
        analysis_group = QGroupBox("Analysis Controls")
        analysis_layout = QVBoxLayout(analysis_group)

        # Single frame analysis
        single_layout = QHBoxLayout()
        self.analyze_btn = QPushButton("Analyze Selected Frame")
        self.analyze_btn.clicked.connect(self.analyze_selected_frame)
        self.analyze_btn.setMinimumHeight(30)

        single_layout.addWidget(self.analyze_btn)
        single_layout.addStretch()

        analysis_layout.addLayout(single_layout)
        controls_layout.addWidget(analysis_group)

        # Progress tracking
        progress_group = QGroupBox("Progress")
        progress_layout = QVBoxLayout(progress_group)

        self.progress_label = QLabel("Ready - Select a frame to analyze")
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)

        progress_layout.addWidget(self.progress_label)
        progress_layout.addWidget(self.progress_bar)
        controls_layout.addWidget(progress_group)

        main_splitter.addWidget(controls_widget)

        # Bottom section for results
        results_widget = QWidget()
        results_layout = QVBoxLayout(results_widget)

        # Results display
        results_group = QGroupBox("Analysis Results")
        results_inner_layout = QVBoxLayout(results_group)

        # Results controls
        results_controls = QHBoxLayout()
        self.clear_results_btn = QPushButton("Clear Results")
        self.clear_results_btn.clicked.connect(self.clear_results)

        self.export_results_btn = QPushButton("Export to JSON")
        self.export_results_btn.clicked.connect(self.export_results)

        results_controls.addWidget(self.clear_results_btn)
        results_controls.addWidget(self.export_results_btn)
        results_controls.addStretch()

        self.results_text = QTextEdit()
        self.results_text.setFont(QFont("Consolas", 10))
        self.results_text.setPlaceholderText("Analysis results will appear here...")

        results_inner_layout.addLayout(results_controls)
        results_inner_layout.addWidget(self.results_text)
        results_layout.addWidget(results_group)

        # Uniqueness analysis
        uniqueness_group = QGroupBox("Uniqueness Analysis")
        uniqueness_layout = QVBoxLayout(uniqueness_group)

        uniqueness_controls = QHBoxLayout()
        self.uniqueness_btn = QPushButton("Calculate Uniqueness Scores")
        self.uniqueness_btn.clicked.connect(self.calculate_uniqueness)

        self.save_pickle_btn = QPushButton("Export to Pickle")
        self.save_pickle_btn.clicked.connect(self.export_to_pickle)

        uniqueness_controls.addWidget(self.uniqueness_btn)
        uniqueness_controls.addWidget(self.save_pickle_btn)
        uniqueness_controls.addStretch()

        self.uniqueness_text = QTextEdit()
        self.uniqueness_text.setFont(QFont("Consolas", 10))
        self.uniqueness_text.setPlaceholderText("Uniqueness analysis will appear here...")

        uniqueness_layout.addLayout(uniqueness_controls)
        uniqueness_layout.addWidget(self.uniqueness_text)
        results_layout.addWidget(uniqueness_group)

        main_splitter.addWidget(results_widget)

        # Set splitter proportions (30% controls, 70% results)
        main_splitter.setSizes([300, 700])

    def check_window_availability(self):
        """Check if WidgetInc window is available"""
        if not self.cache_manager.is_window_available():
            QMessageBox.warning(
                self,
                "WidgetInc Window Not Found",
                "The WidgetInc application window was not found.\n\n"
                "Please ensure:\n"
                "1. WidgetInc.exe is running\n"
                "2. The application window is visible\n\n"
                "You can still use this tool, but frame analysis will not work until the window is detected.",
            )
            self.progress_label.setText("Warning: WidgetInc window not detected")

    def load_frames(self):
        """Load frames from database into dropdown"""
        try:
            # Load from frames database directly
            frames_db_path = Path(__file__).parent.parent.parent / "config" / "data" / "frames_database.json"

            if not frames_db_path.exists():
                self.progress_label.setText("Error: frames_database.json not found")
                return

            with open(frames_db_path, "r", encoding="utf-8") as f:
                frames_data = json.load(f)

            self.frame_combo.clear()
            frames_count = 0

            for frame in frames_data.get("frames", []):
                frame_name = frame.get("name", "Unknown")
                frame_id = frame.get("id", "Unknown")
                display_name = f"{frame_id} - {frame_name}"

                self.frame_combo.addItem(display_name, frame)
                frames_count += 1

            self.progress_label.setText(f"Loaded {frames_count} frames from database")

        except Exception as e:
            self.progress_label.setText(f"Error loading frames: {str(e)}")

    def analyze_selected_frame(self):
        """Analyze the currently selected frame"""
        if self.frame_combo.currentData() is None:
            QMessageBox.warning(self, "No Selection", "Please select a frame to analyze.")
            return

        if not self.cache_manager.is_window_available():
            QMessageBox.warning(
                self,
                "Window Not Available",
                "WidgetInc window is not available. Please ensure the application is running.",
            )
            return

        frame_data = self.frame_combo.currentData()
        self.start_analysis(frame_data)

    def start_analysis(self, frame_data):
        """Start analysis in worker thread"""
        if self.worker and self.worker.isRunning():
            self.progress_label.setText("Analysis already running...")
            return

        self.analyze_btn.setEnabled(False)
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, 0)  # Indeterminate

        self.worker = AnalysisWorker(frame_data, self.analysis_engine)
        self.worker.finished.connect(self.analysis_complete)
        self.worker.error.connect(self.analysis_error)
        self.worker.start()

    def analysis_complete(self, result):
        """Handle single analysis completion"""
        self.analyze_btn.setEnabled(True)
        self.progress_bar.setVisible(False)

        # Always save result to database for comparison
        self.analysis_db.save_analysis(result)

        # Display result
        self.display_analysis_result(result)

        # Auto-advance to next frame
        current_index = self.frame_combo.currentIndex()
        if current_index < self.frame_combo.count() - 1:
            self.frame_combo.setCurrentIndex(current_index + 1)
            self.progress_label.setText("Analysis complete - Advanced to next frame")
        else:
            self.progress_label.setText("Analysis complete - All frames analyzed")

    def analysis_error(self, error_msg):
        """Handle analysis error"""
        self.analyze_btn.setEnabled(True)
        self.progress_bar.setVisible(False)

        QMessageBox.critical(self, "Analysis Error", f"Analysis failed:\n\n{error_msg}")
        self.progress_label.setText(f"Error: {error_msg}")

    def display_analysis_result(self, result):
        """Display analysis result in text area"""
        text = f"Frame: {result['frame_name']} (ID: {result['frame_id']})\n"
        text += f"Resolution: {result['resolution']}\n"
        text += "Left Border:\n"
        text += f"  - Average Color: {result['left_border']['average_color']}\n"
        text += f"  - Dominant Colors: {result['left_border']['dominant_colors'][:3]}\n"
        text += f"  - Color Variance: {result['left_border']['color_variance']:.2f}\n"
        text += f"  - Signature: {result['left_border']['signature'][:16]}...\n"
        text += "Right Border:\n"
        text += f"  - Average Color: {result['right_border']['average_color']}\n"
        text += f"  - Dominant Colors: {result['right_border']['dominant_colors'][:3]}\n"
        text += f"  - Color Variance: {result['right_border']['color_variance']:.2f}\n"
        text += f"  - Signature: {result['right_border']['signature'][:16]}...\n"
        text += f"Analysis Time: {result['timestamp']}\n"
        text += f"{'-' * 60}\n\n"

        self.results_text.append(text)

        # Auto-scroll to bottom
        cursor = self.results_text.textCursor()
        cursor.movePosition(cursor.MoveOperation.End)
        self.results_text.setTextCursor(cursor)

    def clear_results(self):
        """Clear the results display"""
        self.results_text.clear()
        self.uniqueness_text.clear()
        self.progress_label.setText("Results cleared")

    def export_results(self):
        """Export current analysis database to JSON file"""
        try:
            all_results = self.analysis_db.get_all_analyses()
            if not all_results:
                QMessageBox.information(self, "No Data", "No analysis results to export.")
                return

            # Export to logs/reports using new export method
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            report_content = json.dumps(all_results, indent=2, ensure_ascii=False)
            export_path = self.analysis_db.export_report(report_content, f"border_analysis_export_{timestamp}.json")

            QMessageBox.information(self, "Export Complete", f"Results exported to:\n{export_path}")
            self.progress_label.setText(f"Exported {len(all_results)} results to reports")

        except Exception as e:
            QMessageBox.critical(self, "Export Error", f"Failed to export results:\n{str(e)}")

    def calculate_uniqueness(self):
        """Calculate and display uniqueness scores for all analyzed frames"""
        scores = self.analysis_db.calculate_uniqueness_scores()

        if not scores:
            self.uniqueness_text.setText("No analysis data available.\nPlease analyze some frames first.")
            return

        # Sort by uniqueness score (higher = more unique/distinctive)
        sorted_scores = sorted(scores.items(), key=lambda x: x[1], reverse=True)

        text = "Frame Uniqueness Analysis\n"
        text += "=" * 50 + "\n\n"
        text += "Uniqueness Score: Higher values = more distinctive borders\n"
        text += "Lower values = more similar to other frames\n\n"

        for frame_name, score in sorted_scores:
            status = "HIGHLY UNIQUE" if score > 0.7 else "MODERATELY UNIQUE" if score > 0.3 else "SIMILAR TO OTHERS"
            text += f"{frame_name:<25} | Score: {score:.3f} | {status}\n"

        text += "\n" + "=" * 50 + "\n"
        text += f"Total frames analyzed: {len(scores)}\n"
        text += f"Average uniqueness: {sum(scores.values()) / len(scores):.3f}\n"

        # Identify potential problems
        similar_frames = [name for name, score in scores.items() if score < 0.2]
        if similar_frames:
            text += "\nFrames with low uniqueness (may need additional analysis):\n"
            for frame in similar_frames:
                text += f"- {frame}\n"

        self.uniqueness_text.setText(text)
        self.progress_label.setText(f"Uniqueness calculated for {len(scores)} frames")

    def export_to_pickle(self):
        """Export analysis data to pickle format for frame detection"""
        try:
            if not self.analysis_db.get_all_analyses():
                QMessageBox.warning(self, "Export Failed", "No analysis data available to export.")
                return

            pickle_path = self.analysis_db.export_to_pickle()
            QMessageBox.information(
                self,
                "Pickle Export Complete",
                f"Border analysis data exported to pickle format:\n{pickle_path}\n\n"
                "This file can be used for frame detection algorithms.",
            )
            self.progress_label.setText("Exported to pickle format for frame detection")

        except Exception as e:
            QMessageBox.critical(self, "Pickle Export Error", f"Failed to export to pickle:\n{str(e)}")


def main():
    """Main application entry point"""
    app = QApplication(sys.argv)

    # Set application properties
    app.setApplicationName("Frame Border Analysis Tool")
    app.setApplicationVersion("1.0")
    app.setOrganizationName("Widget Automation Tool")

    # Create and show main window
    window = FrameAnalyzerWindow()
    window.show()

    # Run application
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
