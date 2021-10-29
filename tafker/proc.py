# coding: utf-8

import re

import psutil

from tafker.logger import LOGGER


def pgrep(name, ignore_case=True):
    LOGGER.debug(f"Searching for process named {name}")
    regex = re.compile(name, re.IGNORECASE if ignore_case else 0)

    for proc in psutil.process_iter(["pid", "cmdline"]):
        try:
            if re.search(regex, " ".join(proc.cmdline())):
                return proc
        except psutil.NoSuchProcess as exc:
            # should be safe to ignore.
            continue
