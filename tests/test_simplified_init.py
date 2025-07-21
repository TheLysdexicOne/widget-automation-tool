"""
Test Simplified Initialization

Tests the cleaned up initialization code to ensure it works correctly.
"""

from unittest.mock import patch

from utility.status_manager import StatusManager, ApplicationState


class TestSimplifiedStatusManager:
    """Test simplified StatusManager functionality."""

    def test_status_manager_init(self):
        """Test StatusManager initializes correctly."""
        sm = StatusManager()
        assert sm.current_state == ApplicationState.INACTIVE
        assert sm.has_scene_recognition is False
        assert sm.has_automation_logic is False
        assert sm.target_window_found is False
        assert sm.win32_available is False

    def test_capability_updates(self):
        """Test capability updates trigger state detection."""
        sm = StatusManager()

        # Test WIN32 capability
        sm.update_capabilities(win32_available=True)
        assert sm.win32_available is True
        assert sm.current_state == ApplicationState.INACTIVE  # Still no target window

        # Test target window found - should go to ATTENTION now
        sm.update_capabilities(target_window=True)
        assert sm.target_window_found is True
        assert (
            sm.current_state == ApplicationState.ATTENTION
        )  # Now has target window    def test_state_detection_logic(self):
        """Test state detection logic works correctly."""
        sm = StatusManager()

        # Test ERROR state
        sm.update_capabilities(win32_available=False)
        assert sm.current_state == ApplicationState.ERROR

        # Test INACTIVE state (no target window)
        sm.update_capabilities(win32_available=True, target_window=False)
        assert sm.current_state == ApplicationState.INACTIVE

        # Test ATTENTION state (target window found, no scene recognition)
        sm.update_capabilities(target_window=True, scene_recognition=False)
        assert sm.current_state == ApplicationState.ATTENTION

        # Test ATTENTION state (scene recognition but no automation)
        sm.update_capabilities(scene_recognition=True, automation_logic=False)
        assert sm.current_state == ApplicationState.ATTENTION

        # Test READY state (both scene recognition and automation)
        sm.update_capabilities(automation_logic=True)
        assert sm.current_state == ApplicationState.READY

    def test_force_state_detection(self):
        """Test force state detection works."""
        sm = StatusManager()
        sm.update_capabilities(win32_available=True, target_window=True)

        current_state = sm.current_state
        sm.force_state_detection()
        # Should maintain same state since nothing changed
        assert sm.current_state == current_state


class TestSimplifiedMain:
    """Test simplified main.py functionality."""

    @patch("src.main.logging.basicConfig")
    @patch("pathlib.Path.mkdir")
    def test_logging_setup(self, mock_mkdir, mock_basicConfig):
        """Test simplified logging setup."""
        from src.main import setup_logging

        # Test debug mode
        logger = setup_logging(debug=True)
        assert logger is not None
        mock_basicConfig.assert_called()

        # Test normal mode
        logger = setup_logging(debug=False)
        assert logger is not None

    def test_argument_parsing(self):
        """Test argument parsing works correctly."""
        from src.main import parse_arguments

        # Mock sys.argv to test argument parsing
        with patch("sys.argv", ["main.py", "--debug", "--target", "TestApp.exe"]):
            args = parse_arguments()
            assert args.debug is True
            assert args.target == "TestApp.exe"


def test_imports_work():
    """Test that all imports work correctly after simplification."""
    # Test status manager import
    from utility.status_manager import StatusManager, ApplicationState

    assert StatusManager is not None
    assert ApplicationState.ACTIVE.value == "active"

    # Test main imports
    from src.main import setup_logging, parse_arguments

    assert setup_logging is not None
    assert parse_arguments is not None
