# coding: utf-8
import re
from typing import Optional

from ewmh import EWMH
from Xlib.display import Display
from Xlib.error import BadWindow
from Xlib.xobject.drawable import Window

from tafker.logger import LOGGER


def check_window(
    window: Window,
    regex_name: re.Pattern,
    regex_cls: Optional[re.Pattern],
):
    try:
        # Check window classes
        if regex_cls:
            matched = False
            wm_class = window.get_wm_class()
            if not wm_class:
                return False
            for cl_class in wm_class:
                if re.search(regex_cls, cl_class):
                    matched = True
                    break
            if not matched:
                return False

        # Search for target window name
        wm_name = window.get_wm_name()
        if not wm_name:
            return False
        return True if re.search(regex_name, wm_name) else False
    except BadWindow as exc:
        # Some windows are bad. Should be safe to ignore™
        return False


def find_windows(
    name: str,
    cls: Optional[str] = None,
    ignore_case: bool = True,
    exact_match: bool = False,
    only_visible: bool = True,
) -> Optional[Window]:
    LOGGER.debug(f"Searching for window named {name} (class: {cls})")
    regex_name = re.compile(
        name if not exact_match else f"^{name}$",
        re.IGNORECASE if ignore_case else 0,
    )
    regex_cls = (
        re.compile(
            cls if not exact_match else f"^{cls}$",
            re.IGNORECASE if ignore_case else 0,
        )
        if cls
        else None
    )

    res = []
    wm = EWMH()

    clients = wm.getClientList()
    if not only_visible:
        display = Display()
        root = display.screen().root
        root_children = root.query_tree().children

        # FIXME Get rid of python-ewmh here
        clients = list(set(clients + root_children))

    for client in clients:
        if check_window(client, regex_name, regex_cls):
            res.append(client)

    return res
