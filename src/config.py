import os
import sys
from typing import Optional

import structlog

logger = structlog.get_logger()

_current_config: Optional["DashboardConfig"] = None


class DashboardConfig:
    def __init__(self) -> None:
        ics_url = os.getenv("ICS_URL")
        if not ics_url:
            logger.error("ICS_URL needs to be set.")
            sys.exit(1)
        self.ICS_URL: str = ics_url

        self.DISPLAY_TZ: str = os.getenv("DISPLAY_TZ", "America/Los_Angeles")
        self.IMAGE_HEIGHT: int = int(os.getenv("IMAGE_HEIGHT", "825"))
        self.IMAGE_WIDTH: int = int(os.getenv("IMAGE_WIDTH", "1200"))
        self.SHOW_CALENDAR_NAME: bool = os.getenv("SHOW_CALENDAR_NAME", "False").lower() == "true"
        self.USE_24H_FORMAT: bool = os.getenv("USE_24H_FORMAT", "True").lower() == "true"

    @classmethod
    def get_config(cls) -> "DashboardConfig":
        global _current_config
        if _current_config is None:
            _current_config = DashboardConfig()
        return _current_config
