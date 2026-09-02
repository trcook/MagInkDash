import os
import pytest
import sys
from unittest.mock import patch


# Add the src directory to the path so we can import the modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from config import DashboardConfig


class TestDashboardConfig:
    """Test suite for DashboardConfig class."""

    def setup_method(self):
        """Clear any existing global config before each test."""
        import config

        config._current_config = None

    @patch.dict(
        os.environ,
        {
            "ICS_URL": "https://example.com/calendar.ics",
        },
        clear=True,
    )
    def test_init_with_minimal_required_env_vars(self):
        """Test DashboardConfig initialization with only required environment variables."""
        config = DashboardConfig()

        # Required variables
        assert config.ICS_URL == "https://example.com/calendar.ics"

        # Default values
        assert config.DISPLAY_TZ == "America/Los_Angeles"
        assert config.IMAGE_WIDTH == 1200
        assert config.IMAGE_HEIGHT == 825
        assert config.SHOW_CALENDAR_NAME == False
        assert config.USE_24H_FORMAT == True

    @patch.dict(
        os.environ,
        {
            "ICS_URL": "https://example.com/calendar.ics",
            "DISPLAY_TZ": "America/New_York",
            "IMAGE_WIDTH": "1600",
            "IMAGE_HEIGHT": "900",
            "SHOW_CALENDAR_NAME": "TRUE",
            "USE_24H_FORMAT": "false",
        },
        clear=True,
    )
    def test_init_with_all_env_vars_set(self):
        """Test DashboardConfig initialization with all environment variables set."""
        config = DashboardConfig()

        assert config.ICS_URL == "https://example.com/calendar.ics"
        assert config.DISPLAY_TZ == "America/New_York"
        assert config.IMAGE_WIDTH == 1600
        assert config.IMAGE_HEIGHT == 900
        assert config.SHOW_CALENDAR_NAME == True
        assert config.USE_24H_FORMAT == False

    @patch.dict(os.environ, {}, clear=True)
    @patch("config.logger")
    def test_missing_ics_url_exits(self, mock_logger):
        """Test that missing ICS_URL causes system exit."""
        with pytest.raises(SystemExit) as exc_info:
            DashboardConfig()

        assert exc_info.value.code == 1
        mock_logger.error.assert_called_with("ICS_URL needs to be set.")

    @patch.dict(
        os.environ,
        {
            "ICS_URL": "https://example.com/calendar.ics",
            "SHOW_CALENDAR_NAME": "True",
            "USE_24H_FORMAT": "TRUE",
        },
        clear=True,
    )
    def test_boolean_env_vars_true_values(self):
        """Test boolean environment variables with various true values."""
        config = DashboardConfig()

        assert config.SHOW_CALENDAR_NAME == True
        assert config.USE_24H_FORMAT == True

    @patch.dict(
        os.environ,
        {
            "ICS_URL": "https://example.com/calendar.ics",
            "SHOW_CALENDAR_NAME": "NotTrue",
            "USE_24H_FORMAT": "False",
        },
        clear=True,
    )
    def test_boolean_env_vars_false_values(self):
        """Test boolean environment variables with various false values."""
        config = DashboardConfig()

        assert config.SHOW_CALENDAR_NAME == False
        assert config.USE_24H_FORMAT == False

    @patch.dict(
        os.environ,
        {
            "ICS_URL": "https://example.com/calendar.ics",
            "IMAGE_WIDTH": "1",
            "IMAGE_HEIGHT": "1",
        },
        clear=True,
    )
    def test_integer_edge_cases(self):
        """Test integer environment variables with edge case values."""
        config = DashboardConfig()

        assert config.IMAGE_WIDTH == 1
        assert config.IMAGE_HEIGHT == 1

    @patch("config.DashboardConfig.__init__")
    def test_get_config_singleton_pattern(self, mock_init):
        """Test that get_config() implements singleton pattern correctly."""
        mock_init.return_value = None

        # First call should create instance
        config1 = DashboardConfig.get_config()
        assert mock_init.call_count == 1

        # Second call should return same instance
        config2 = DashboardConfig.get_config()
        assert mock_init.call_count == 1  # Should not be called again
        assert config1 is config2

    def test_get_config_returns_same_instance(self):
        """Test that get_config returns the same instance on multiple calls."""
        with patch.dict(
            os.environ,
            {
                "ICS_URL": "https://example.com/calendar.ics",
            },
            clear=True,
        ):
            config1 = DashboardConfig.get_config()
            config2 = DashboardConfig.get_config()

            assert config1 is config2
            assert id(config1) == id(config2)
