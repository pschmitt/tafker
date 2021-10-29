# coding: utf-8

import re

import psutil


def pgrep(name):
    for proc in psutil.process_iter(["pid", "cmdline"]):
        if name in " ".join(proc.cmdline()):
            return proc.pid()
