"""
This project is designed for the Inkplate 10 display. However, since the server code is only generating an image, it can
be easily adapted to other display sizes and resolution by adjusting the config settings, HTML template and
CSS stylesheet.
"""

import datetime as dt
import tempfile
import time
from typing import Any, Dict, List

import pytz
import structlog
import uvicorn
from fastapi import FastAPI
from fastapi.responses import FileResponse

from config import DashboardConfig
from ics_cal.ics import IcsModule
from render.render import RenderHelper

cfg = DashboardConfig.get_config()

app = FastAPI(title="Family E-Ink Dashboard Server", version="0.10.0")

logger = structlog.get_logger()

calModule = IcsModule()


@app.get("/health")
def health_check() -> Dict[str, Any]:
    return {"status": "ok"}


@app.get(
    "/test",
    summary="Background image for testing",
)
def get_background() -> FileResponse:
    return FileResponse("src/render/background.png", media_type="image/png")


@app.get("/image", summary="Rendered dashboard image")
def get_image() -> FileResponse:
    start_time = time.time()
    logger.info("Retrieving data...")

    local_timezone = pytz.timezone(cfg.DISPLAY_TZ)
    currTime = dt.datetime.now(local_timezone)
    today = currTime.date()
    week_start = today - dt.timedelta(days=(today.weekday() + 1) % 7)
    calStartDatetime = local_timezone.localize(dt.datetime.combine(week_start, dt.time(0, 0, 0)))
    calEndDatetime = calStartDatetime + dt.timedelta(days=7, seconds=-1)

    events: Dict[dt.date, List[Dict[str, Any]]] = calModule.get_events(
        cfg.ICS_URL, calStartDatetime, calEndDatetime, cfg.DISPLAY_TZ
    )

    # Remove today's past events
    if today in events:
        filtered_events = []
        for e in events[today]:
            end_datetime = e["endDatetime"]
            if end_datetime.tzinfo is None:
                end_datetime = local_timezone.localize(end_datetime)
            if end_datetime >= currTime:
                filtered_events.append(e)
        if filtered_events:
            events[today] = filtered_events
        else:
            del events[today]

    end_time = time.time()
    logger.info(f"Completed data retrieval in {round(end_time - start_time, 3)} seconds.")

    # TODO: delete=False leads to accumulating temporary files in /tmp but is currently needed because the FileResponse is async.
    with tempfile.NamedTemporaryFile(suffix=".png", delete_on_close=False, delete=False) as tf:
        start_time = time.time()
        logger.info("Generating image...")

        renderService = RenderHelper(cfg)
        renderService.process_inputs(currTime, events, tf.name)

        end_time = time.time()
        logger.info(
            f"Completed image generation in {round(end_time - start_time, 3)} seconds, serving image now."
        )

        return FileResponse(tf.name, media_type="image/png")


if __name__ == "__main__":
    logger.info("Starting web server...")
    config = uvicorn.Config(app, host="127.0.0.1", port=5000, log_level="debug")
    server = uvicorn.Server(config)
    server.run()
