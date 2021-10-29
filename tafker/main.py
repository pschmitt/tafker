#!/usr/bin/env python
# coding: utf-8

import argparse
import datetime
import logging
import pathlib
import sys
from contextvars import ContextVar
from posixpath import join
from time import sleep

import anyio
import psutil
import yaml
from rich.console import Console
from rich.logging import RichHandler
from xdg import xdg_config_home

from tafker.logger import LOGGER
from tafker.proc import pgrep

console = Console()
APP_STATES = ContextVar("STATE")


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-d", "--debug", action="store_true", default=False, help="DEBUG logging"
    )
    parser.add_argument(
        "-c",
        "--config",
        type=lambda p: pathlib.Path(p).absolute(),
        default=pathlib.Path.joinpath(xdg_config_home(), "tafker.yaml"),
        help="Path to the config file",
    )
    return parser.parse_args()


async def check_application(name: str, appconfig: dict):
    proc = pgrep(appconfig.get("process_name", name))
    states = APP_STATES.get()
    previous_state = states.get(name)
    if proc:
        LOGGER.info(f"🆙 {name} is running (Previous state: previous_state)")
        LOGGER.debug(f"🆙 {proc.cmdline()} [PID: {proc.pid}]")

        if previous_state and previous_state != "running":
            LOGGER.warning(f"Starting start commands for {name}")
            for cmd in appconfig.get("scripts", {}).get("start", []):
                await anyio.run_process(cmd)
        states[name] = "running"
    else:
        LOGGER.info(f"🛑 {name} is *not* running (Previous state: {previous_state})")
        if previous_state and previous_state != "stopped":
            LOGGER.warning(f"Starting stop commands for {name}")
            for cmd in appconfig.get("scripts", {}).get("stop", []):
                await anyio.run_process(cmd)
        states[name] = "stopped"

    APP_STATES.set(states)
    # DEBUG
    # await anyio.sleep(2)


async def process_apps(config: dict):
    apps = config.get("apps", [])
    async with anyio.create_task_group() as tg:
        for app in apps:
            tg.start_soon(check_application, app, apps[app])


def watch_loop(config: dict):
    APP_STATES.set({})
    tick_interval = config.get("interval", 1)
    try:
        while True:
            try:
                tick_start = datetime.datetime.now()
                anyio.run(process_apps, config, backend_options={"use_uvloop": True})
                delta = datetime.datetime.now() - tick_start
                # Don't update too fast!
                if delta.seconds < tick_interval:
                    LOGGER.debug("Sleep to avoid going too fast")
                    sleep(tick_interval - delta.seconds)
                LOGGER.debug(
                    f"Tick. The last iteration took {delta.seconds} second(s)."
                )
            except Exception as exc:
                if isinstance(exc, KeyboardInterrupt):
                    raise exc
                console.print_exception(show_locals=True)
    except KeyboardInterrupt:
        LOGGER.debug("Caught KeyboardInterrupt")
        return 130


def parse_config(path: str = None):
    if not path:
        xdg_home = xdg_config_home()
        search_paths = [
            pathlib.Path.joinpath(xdg_home, "tafker.yaml"),
            pathlib.Path.joinpath(xdg_home, "tafker.yml"),
            pathlib.Path.joinpath(xdg_home, "tafker/tafker.yaml"),
            pathlib.Path.joinpath(xdg_home, "tafker/tafker.yml"),
        ]
        for p in search_paths:
            LOGGER.info(f"Search config in {p}")
            if p.exists():
                path = p
                break

    if not path:
        raise RuntimeError("No config found.")

    with open(path, "r") as f:
        config = yaml.load(f.read(), Loader=yaml.CLoader)

    return config


def main():
    args = parse_args()

    logging.basicConfig(
        level="DEBUG" if args.debug else "INFO",
        format="%(message)s",
        datefmt="[%X]",
        handlers=[RichHandler()],
    )

    LOGGER.debug(f"Args: {args}")
    config = parse_config(args.config)
    return watch_loop(config)


if __name__ == "__main__":
    rc = main()
    sys.exit(rc if isinstance(rc, int) else 9)
