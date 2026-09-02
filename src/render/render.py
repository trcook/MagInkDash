"""
This script essentially generates a HTML file of the calendar I wish to display. It then fires up a headless Chrome
instance, sized to the resolution of the eInk display and takes a screenshot.
"""

import datetime as dt
import os
import pathlib
import subprocess
from time import sleep
from typing import Any, Dict, List

import structlog
from jinja2 import Environment, FileSystemLoader
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By

from config import DashboardConfig


class RenderHelper:
    def __init__(self, cfg: DashboardConfig) -> None:
        self.logger = structlog.get_logger()
        self.currPath = str(pathlib.Path(__file__).parent.absolute())
        self.htmlFile = "file://" + self.currPath + "/dashboard.html"
        self.cfg = cfg

    def set_viewport_size(self, driver: webdriver.Chrome) -> None:
        # Extract the current window size from the driver
        current_window_size = driver.get_window_size()

        # Extract the client window size from the html tag
        html = driver.find_element(By.TAG_NAME, "html")
        inner_width = int(html.get_attribute("clientWidth") or "0")
        inner_height = int(html.get_attribute("clientHeight") or "0")

        # "Internal width you want to set+Set "outer frame width" to window size
        target_width = self.cfg.IMAGE_WIDTH + (current_window_size["width"] - inner_width)
        target_height = self.cfg.IMAGE_HEIGHT + (current_window_size["height"] - inner_height)

        driver.set_window_rect(width=target_width, height=target_height)

    def get_screenshot(self, path_to_server_image: str) -> None:
        opts = Options()
        opts.add_argument("--disable-dev-shm-usage")
        opts.add_argument("--disable-gpu")
        opts.add_argument("--disable-extensions")
        opts.add_argument("--force-device-scale-factor=1")
        opts.add_argument("--headless")
        opts.add_argument("--hide-scrollbars")
        opts.add_argument("--no-sandbox")

        # Try to automatically locate chromedriver, source: https://github.com/fdmarcin/MagInkDash-updated
        try:
            chromedriver_path = (
                subprocess.check_output(["which", "chromedriver"]).decode("utf-8").strip()
            )
            self.logger.info(f"Found chromedriver at: {chromedriver_path}")
        except (subprocess.SubprocessError, FileNotFoundError):
            # Default paths to try if 'which' command fails
            possible_paths = [
                "/usr/bin/chromedriver",
                "/usr/local/bin/chromedriver",
                "/usr/lib/chromium-browser/chromedriver",
            ]

            chromedriver_path = None
            for path in possible_paths:
                if os.path.exists(path) and os.access(path, os.X_OK):
                    chromedriver_path = path
                    self.logger.info(f"Found chromedriver at default location: {chromedriver_path}")
                    break

            if not chromedriver_path:
                self.logger.error(
                    "Could not find chromedriver. Please install it with 'sudo apt-get install chromium-chromedriver'"
                )
                raise FileNotFoundError("chromedriver executable not found in PATH")

        # Use the discovered chromedriver path
        service = Service(chromedriver_path)

        try:
            driver = webdriver.Chrome(service=service, options=opts)
            self.set_viewport_size(driver)
            driver.get(self.htmlFile)
            sleep(1)
            driver.get_screenshot_as_file(self.currPath + "/dashboard.png")
            driver.get_screenshot_as_file(path_to_server_image)
            driver.quit()  # Make sure to quit the driver to free resources
            self.logger.debug(f"Screenshot captured and saved to file {path_to_server_image}.")
        except Exception as e:
            self.logger.error(f"Error taking screenshot: {str(e)}")
            raise

    def process_inputs(
        self,
        current_time: dt.datetime,
        events: Dict[dt.date, List[Dict[str, Any]]],
        path_to_server_image: str,
    ) -> None:
        # Read html template
        environment = Environment(loader=FileSystemLoader(self.currPath))
        dashboard_template = environment.get_template("dashboard_template.html.j2")

        current_date = current_time.date()

        # The week starts on Sunday
        week_start = current_date - dt.timedelta(days=(current_date.weekday() + 1) % 7)

        week_days = []
        for i in range(7):
            day = week_start + dt.timedelta(days=i)
            week_days.append(
                {
                    "name": day.strftime("%A"),
                    "number": day.strftime("%-d"),
                    "is_today": day == current_date,
                    "events": self.build_events_html(events.get(day, [])),
                }
            )

        # Write the file
        htmlFile = open(self.currPath + "/dashboard.html", "w")
        htmlFile.write(
            dashboard_template.render(
                update_time=f"{current_time.strftime('%B %-d')}, {self.format_time(current_time)}",
                day=current_date.strftime("%-d"),
                month=current_date.strftime("%B %Y"),
                weekday=current_date.strftime("%A"),
                week_days=week_days,
                today_events=self.build_today_event_list(events.get(current_date, [])),
            )
        )
        htmlFile.close()

        self.get_screenshot(path_to_server_image)

    def build_today_event_list(self, day_events: List[Dict[str, Any]]) -> List[str]:
        # Small bulleted summary of today's events shown in the header
        items = []
        for event in day_events[:3]:
            if event["startDatetime"].time() == dt.time(0, 0, 0):
                label = event["summary"]
            else:
                label = f"{self.format_time(event['startDatetime'])} {event['summary']}"
            if len(label) > 24:
                label = label[:23] + "…"
            items.append(label)
        return items

    def build_events_html(self, day_events: List[Dict[str, Any]]) -> str:
        if not day_events:
            return '<div class="event event-empty">&ndash;</div>'
        cal_events_text = ""
        for event in day_events:
            cal_events_text += '<div class="event">'
            # All-day events or continuations from yesterday start at midnight
            if event["startDatetime"].time() == dt.time(0, 0, 0):
                cal_events_text += event["summary"]
            else:
                cal_events_text += (
                    '<span class="event-time">'
                    + self.format_time(event["startDatetime"])
                    + "</span> "
                    + event["summary"]
                )
            # Some clients set the location to empty string
            if "location" in event and event["location"] != "":
                cal_events_text += (
                    '<span class="event-location"> at ' + event["location"] + "</span>"
                )
            if self.cfg.SHOW_CALENDAR_NAME and event["calendarName"] is not None:
                cal_events_text += (
                    '<span class="event-calendar-name"> (' + event["calendarName"] + ")</span>"
                )
            cal_events_text += "</div>\n"
        return cal_events_text

    def format_time(self, datetimeObj: dt.datetime) -> str:
        if self.cfg.USE_24H_FORMAT:
            return datetimeObj.strftime("%H:%M")
        else:
            return datetimeObj.strftime("%-I:%M%p").replace(":00", "").lower()
