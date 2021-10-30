# coding: utf-8

import asyncio
import subprocess
from typing import Optional


import anyio
from anyio import to_process, to_thread

from tafker.const import TAFKER_CMD_PREFIX
from tafker.logger import LOGGER


def run_commands(cmds: list, timeout: Optional[int] = None):
    res = []
    for cmd in cmds:
        LOGGER.info(f"Spawning $ {cmd}")
        try:
            # anyio.run_process(cmd)
            res.append(subprocess.run(cmd, shell=True))
        except Exception as exc:
            LOGGER.error(f"Something went wrong while running {cmd}: {exc}")
    return res


async def async_run_commands(cmds: list):
    res = []
    for cmd in cmds:
        try:
            res.append(subprocess.run(cmd, shell=True))
            # res.append(subprocess.Popen(cmd, shell=True))
        except Exception as exc:
            LOGGER.error(f"Something went wrong while running {cmd}: {exc}")
    return res


async def asyncio_run_commands(cmds: list):
    procs = []
    for cmd in cmds:
        proc = await asyncio.create_subprocess_shell(
            f"{TAFKER_CMD_PREFIX} {cmd}",
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
        )
        procs.append(proc)
    # TODO log stdout and stderr
    return procs


async def anyio_run_commands(cmds: list, timeout: int = 1):
    if not cmds:
        LOGGER.debug(f"Nothing to do here")
        return

    # async with anyio.create_task_group() as tg:
    #     for cmd in cmds:
    #         with anyio.move_on_after(timeout) as scope:
    #             tg.start_soon(async_run_commands, [f"{cmd} &"])
    #         if scope.cancel_called:
    #             LOGGER.warning(f"Timeout reached")

    # FIXME This is blocking!
    # for cmd in cmds:
    #     try:
    #         await anyio.run_process(f"{cmd} &")
    #     except Exception as exc:
    #         LOGGER.error(f"Something went wrong while running {cmd}: {exc}")

    # for cmd in cmds:
    # await to_thread.run_sync(run_commands, cmds)
    # await to_process.run_sync(run_commands, cmds)

    # try:
    #     await to_process.run_sync(run_commands, cmds)
    # except Exception as exc:
    #     LOGGER.error(f"Something went wrong while running {cmds}: {exc}")
