"""Async utilities for skill_fleet modules.

This module provides utilities for running async code in sync contexts.
"""

from __future__ import annotations

import asyncio
from typing import Any, Callable, TypeVar

T = TypeVar("T")


def run_async(coro_func: Callable[[], Any]) -> Any:
    """Run an async coroutine function in a sync context.

    This utility handles running async functions from sync code by:
    1. Trying to use the current event loop if one exists
    2. Creating a new event loop if none exists
    
    Args:
        coro_func: A callable that returns a coroutine (e.g., lambda: async_func())
    
    Returns:
        The result of the coroutine execution
    
    Example:
        >>> result = run_async(lambda: my_async_function())
    """
    coro = coro_func()
    
    try:
        # Try to get the current event loop
        loop = asyncio.get_event_loop()
        if loop.is_running():
            # If the loop is already running, we need to use a different approach
            # This can happen in nested async contexts
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor() as pool:
                return pool.submit(asyncio.run, coro).result()
        else:
            return loop.run_until_complete(coro)
    except RuntimeError:
        # No event loop exists, create a new one
        return asyncio.run(coro)
