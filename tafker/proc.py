# coding: utf-8

import re
from typing import Optional, Union

import psutil

from tafker.const import TAFKER_CMD_PREFIX
from tafker.logger import LOGGER


def pgrep(
    name: str, ignore_case: bool = True, fetch_all: bool = False
) -> Optional[Union[list, psutil.Process]]:
    LOGGER.debug(f"Searching for process named {name}")
    regex = re.compile(name, re.IGNORECASE if ignore_case else 0)

    res = []

    for proc in psutil.process_iter(["pid", "cmdline"]):
        try:
            cmdline = " ".join(proc.cmdline())
            # Skip processes we created ourselves
            if not fetch_all and TAFKER_CMD_PREFIX in cmdline:
                continue
            if re.search(regex, cmdline):
                if fetch_all:
                    res.append(proc)
                else:
                    return proc
        except psutil.NoSuchProcess as exc:
            # should be safe to ignore.
            continue

    if fetch_all:
        return res
