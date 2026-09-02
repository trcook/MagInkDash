import datetime as dt
import pytest
import sys
import os

# Add the src directory to the path so we can import the modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from render.render import RenderHelper


class HourMockConfig:
    """12/24 hour mock configuration for testing."""

    def __init__(self, use_24h_format=True):
        self.USE_24H_FORMAT = use_24h_format


class TestRenderHelper:
    """Test suite for RenderHelper class methods."""

    @pytest.mark.parametrize(
        "datetime_obj,expected",
        [
            (dt.datetime(2024, 1, 1, 0, 0), "00:00"),
            (dt.datetime(2024, 1, 1, 9, 30), "09:30"),
            (dt.datetime(2024, 1, 1, 12, 0), "12:00"),
            (dt.datetime(2024, 1, 1, 23, 59), "23:59"),
            (dt.datetime(2024, 1, 1, 14, 5), "14:05"),
        ],
    )
    def test_format_time_24hour_format(self, datetime_obj, expected):
        """Test format_time with 24-hour format."""
        render_helper = RenderHelper(HourMockConfig(use_24h_format=True))

        result = render_helper.format_time(datetime_obj)
        assert result == expected

    @pytest.mark.parametrize(
        "datetime_obj,expected",
        [
            # Midnight cases
            (dt.datetime(2024, 1, 1, 0, 0), "12am"),
            (dt.datetime(2024, 1, 1, 0, 30), "12:30am"),
            # Morning cases
            (dt.datetime(2024, 1, 1, 1, 0), "1am"),
            (dt.datetime(2024, 1, 1, 9, 15), "9:15am"),
            (dt.datetime(2024, 1, 1, 11, 45), "11:45am"),
            # Noon cases
            (dt.datetime(2024, 1, 1, 12, 0), "12pm"),
            (dt.datetime(2024, 1, 1, 12, 30), "12:30pm"),
            # Afternoon/Evening cases
            (dt.datetime(2024, 1, 1, 13, 0), "1pm"),
            (dt.datetime(2024, 1, 1, 15, 20), "3:20pm"),
            (dt.datetime(2024, 1, 1, 23, 59), "11:59pm"),
            # Zero minutes cases
            (dt.datetime(2024, 1, 1, 0, 0), "12am"),
            (dt.datetime(2024, 1, 1, 5, 0), "5am"),
            (dt.datetime(2024, 1, 1, 12, 0), "12pm"),
            (dt.datetime(2024, 1, 1, 18, 0), "6pm"),
        ],
    )
    def test_format_time_12hour_format(self, datetime_obj, expected):
        """Test format_time with 12-hour format."""
        render_helper = RenderHelper(HourMockConfig(use_24h_format=False))

        result = render_helper.format_time(datetime_obj)
        assert result == expected
