"""Generic background-thread runner for device I/O.

Every device layer call (list devices, pull, push, etc.) is blocking USB I/O
and must never run on Qt's main thread - that would freeze the whole window
for however long the operation takes (which, per tonight's manual testing,
can be several seconds even for a simple listing)."""

from __future__ import annotations

from typing import Any, Callable

from PySide6.QtCore import QObject, QThread, Signal


class Worker(QThread):
    succeeded = Signal(object)
    failed = Signal(Exception)

    def __init__(self, fn: Callable[..., Any], *args: Any, **kwargs: Any):
        super().__init__()
        self._fn = fn
        self._args = args
        self._kwargs = kwargs

    def run(self) -> None:
        try:
            result = self._fn(*self._args, **self._kwargs)
        except Exception as exc:  # noqa: BLE001 - deliberately broad, forwarded to the UI
            self.failed.emit(exc)
        else:
            self.succeeded.emit(result)


def run_in_background(
    parent: QObject,
    fn: Callable[..., Any],
    *args: Any,
    on_success: Callable[[Any], None] | None = None,
    on_error: Callable[[Exception], None] | None = None,
    **kwargs: Any,
) -> Worker:
    """Fire-and-forget helper: runs fn(*args, **kwargs) on a background
    QThread and calls on_success/on_error on the main thread when done. The
    returned Worker must be kept alive by the caller (e.g. stored on self)
    until it finishes, or Qt will garbage-collect it mid-run."""
    worker = Worker(fn, *args, **kwargs)
    worker.setParent(parent)
    if on_success is not None:
        worker.succeeded.connect(on_success)
    if on_error is not None:
        worker.failed.connect(on_error)
    worker.start()
    return worker
