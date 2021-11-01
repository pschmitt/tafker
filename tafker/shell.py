# coding: utf-8

import asyncio
import subprocess
import time
from typing import Optional

from tafker.const import TAFKER_CMD_PREFIX
from tafker.logger import LOGGER
from tafker.proc import pgrep


async def asyncio_run_commands(cmds: list, metadata: Optional[dict] = None):
    procs = []
    prefix = TAFKER_CMD_PREFIX
    if metadata:
        for key, val in metadata.items():
            prefix += f" TAFKER_{key.upper()}={val};"
    for cmd in cmds:
        proc = await asyncio.create_subprocess_shell(
            f"{prefix} {cmd}",
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
        )
        procs.append(proc)
    # TODO log stdout and stderr
    return procs


def kill_running_commands(name: str):
    for proc in pgrep(f"TAFKER_NAME={name};", fetch_all=True):
        LOGGER.debug(f"🔪 Killing script for {name}: {' '.join(proc.cmdline())}")
        proc.kill()


async def kill_long_running_commands(max_age: int = 30):
    now = time.time()
    for proc in pgrep(f"TAFKER=1;", fetch_all=True):
        proc_age = now - proc.create_time()
        if proc_age > max_age:
            LOGGER.warning(
                f"⏰ Timed out after {proc_age}s! "
                f"Killing script: {' '.join(proc.cmdline())}"
            )
            proc.kill()
