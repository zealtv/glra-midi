# SPDX-License-Identifier: GPL-3.0-only

"""Shared set-up for the app tests: skip without PySide6, run Qt offscreen, make a home."""

import os
import tempfile
import unittest
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
os.environ.setdefault("QT_QUICK_BACKEND", "software")
os.environ.setdefault("QT_QUICK_CONTROLS_STYLE", "Basic")

try:
    from PySide6.QtGui import QGuiApplication
except ImportError:
    raise unittest.SkipTest("PySide6 not installed (pip install '.[gui]')") from None

from glra_osc import profile as prof
from glra_osc.app import gui

app = QGuiApplication.instance() or QGuiApplication([])


def make_home(testcase, text=None):
    """A temporary home with `profiles/default.toml` (the demo fixture unless `text`) and a
    `current` pointer; the directory goes away with the test."""
    tmp = tempfile.TemporaryDirectory()
    testcase.addCleanup(tmp.cleanup)
    home = Path(tmp.name)
    folder = prof.profiles_dir(home)
    folder.mkdir(parents=True)
    body = gui.DEMO_PROFILE.read_text(encoding="utf-8") if text is None else text
    (folder / "default.toml").write_text(body, encoding="utf-8")
    (prof.app_dir(home) / prof.CURRENT_FILE_NAME).write_text("default\n", encoding="utf-8")
    return home


def write_profile(home, name, text):
    path = prof.profile_path(name, home)
    path.write_text(text, encoding="utf-8")
    return path


def forbid_real_device(testcase):
    """Make any attempt to reach the real pad fail the test (the app tests use fakes only)."""
    from unittest import mock

    def refuse(*args, **kwargs):
        raise AssertionError("a test tried to reach the real pad; use a FakePad")

    for target in (
        "glra_osc.device.backend.enumerate_devices",
        "glra_osc.device.backend.select",
        "glra_osc.device.backend.open_device",
        "glra_osc.lighting.connect",
    ):
        patcher = mock.patch(target, refuse)
        patcher.start()
        testcase.addCleanup(patcher.stop)
