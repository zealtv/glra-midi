# SPDX-License-Identifier: GPL-3.0-only

"""Runs the pad's blocking calls off the UI thread (docs/config-app.md 5.3).

One worker thread, so pad calls never overlap and the window stays responsive during a read or
a write; glra-studio's `worker.py` keeps its device transactions on one thread the same way. The
worker only runs the callable it is handed (`pad.read` or `pad.apply`); it decides nothing about
*whether* to write. Results come back as the `done` signal on the UI thread:
`done(kind, result, error)` with `error` the exception (or None).
"""

from concurrent.futures import ThreadPoolExecutor

from PySide6.QtCore import QObject, Signal


class PadWorker(QObject):
    done = Signal(str, object, object)  # kind, result, error

    def __init__(self, parent=None):
        super().__init__(parent)
        self._pool = ThreadPoolExecutor(max_workers=1, thread_name_prefix="pad")
        self._pending = 0

    @property
    def idle(self):
        return self._pending == 0

    def submit(self, kind, call, *args):
        """Run `call(*args)` on the worker thread; `done(kind, result, error)` follows."""
        self._pending += 1
        self._pool.submit(self._run, kind, call, args)

    def _run(self, kind, call, args):
        result = error = None
        try:
            result = call(*args)
        except Exception as err:  # reported to the UI, never raised on the worker thread
            error = err
        self.done.emit(kind, result, error)

    def finished_one(self):
        """Called by the owner in its `done` slot, on the UI thread."""
        self._pending = max(0, self._pending - 1)

    def shutdown(self):
        self._pool.shutdown(wait=True)
