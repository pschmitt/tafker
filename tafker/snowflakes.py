# coding: utf-8
from typing import Optional

import psutil
from Xlib.xobject.drawable import Window

from tafker.logger import LOGGER
from tafker.proc import pgrep
from tafker.win import find_windows


def zoom_meeting_status() -> Optional[tuple[psutil.Process, Window]]:
    zoom_proc = pgrep("zoom zoommtg://")
    if not zoom_proc:
        return

    zoom_wins = find_windows(
        cls="zoom",
        name="(Zoom Meeting)|(zoom_linux_float_video_window)",
        only_visible=False,
    )
    LOGGER.debug(f"Zoom PID: {zoom_proc.pid} - Windows: {zoom_wins}")
    return (zoom_proc, zoom_wins[0]) if zoom_wins else None
