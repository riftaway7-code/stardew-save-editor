"""Internal helpers shared across the device layer.

Every public function in this package is a plain synchronous function that
runs its own short-lived asyncio event loop via ``run()``. We deliberately do
NOT keep a long-lived event loop across calls (unlike pymobiledevice3's own
CLI, which reuses one loop across an interactive shell session and can hit
"event loop is already running" errors when driven non-interactively - we hit
this exact bug during manual testing). One `asyncio.run()` per operation is
slightly less efficient but far more robust, and this module is always called
from a background thread (never Qt's main thread), so the extra loop
start/stop cost is irrelevant.
"""

from __future__ import annotations

import asyncio
import warnings
from typing import Any, Coroutine, TypeVar

T = TypeVar("T")


def _quiet_exception_handler(loop: asyncio.AbstractEventLoop, context: dict[str, Any]) -> None:
    # pymobiledevice3's lockdown/AFC connections don't always get an explicit
    # close() before our short-lived asyncio.run() loop tears down, which
    # surfaces as harmless "Fatal error on SSL transport" / "Event loop is
    # closed" noise from the transport's own __del__/callback cleanup. These
    # don't indicate a failed operation (the operation itself already
    # returned its result by this point) - swallow them instead of spamming
    # every CLI invocation.
    exc = context.get("exception")
    if isinstance(exc, (OSError, RuntimeError)):
        return
    loop.default_exception_handler(context)


def run(coro: Coroutine[Any, Any, T]) -> T:
    with warnings.catch_warnings():
        # pymobiledevice3's dependency chain warns about the system LibreSSL
        # build on macOS; harmless for our purposes, and noisy in every call.
        warnings.filterwarnings("ignore", message=".*OpenSSL.*")
        loop = asyncio.new_event_loop()
        loop.set_exception_handler(_quiet_exception_handler)
        try:
            return loop.run_until_complete(coro)
        finally:
            loop.close()
