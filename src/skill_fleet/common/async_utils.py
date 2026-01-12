"""Utilities for safely bridging async and sync code.

This project exposes some synchronous wrappers around async DSPy modules.
Calling a sync wrapper from within an already-running event loop can deadlock
if it tries to block on that same loop.

`run_async()` avoids that by:
- Using `asyncio.run()` when no loop is running in the current thread.
- Otherwise executing the coroutine in a dedicated background thread.
"""

from __future__ import annotations

import asyncio
import queue
import threading
from collections.abc import Awaitable, Callable


def run_async[T](factory: Callable[[], Awaitable[T]]) -> T:
    """Run an async callable from synchronous code.

    This is intended for sync wrappers like `forward()` that need to call an
    async implementation like `aforward()`.
    """
    try:
        asyncio.get_running_loop()
    except RuntimeError:
        return asyncio.run(factory())

    result_queue: queue.Queue[tuple[bool, T | BaseException]] = queue.Queue(maxsize=1)

    def _runner() -> None:
        try:
            result_queue.put((True, asyncio.run(factory())))
        except BaseException as exc:
            result_queue.put((False, exc))

    thread = threading.Thread(target=_runner, daemon=True)
    thread.start()
    ok, payload = result_queue.get()
    thread.join()

    if ok:
        return payload  # type: ignore[return-value]
    raise payload  # type: ignore[misc]
