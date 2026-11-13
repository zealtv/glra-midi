# SPDX-License-Identifier: GPL-3.0-only

"""Test package. Every test runs with HOME pointing at a throwaway folder, so nothing that
resolves `Path.home()` (the profile folder, its pre-rename migration, backups) can reach the
real `~/Library/Application Support` (loom:rename-code, 2026-11-13)."""

import atexit
import os
import shutil
import tempfile

_HOME = tempfile.mkdtemp(prefix="glra-midi-test-home-")
os.environ["HOME"] = _HOME
atexit.register(shutil.rmtree, _HOME, ignore_errors=True)
