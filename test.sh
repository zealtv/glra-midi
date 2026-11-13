#!/bin/sh
# SPDX-License-Identifier: GPL-3.0-only
# Lint + tests. Run from anywhere; uses the repo's .venv.
set -e
cd "$(dirname "$0")"
PY=.venv/bin/python
$PY -m ruff check glra_midi tests
$PY -m ruff format --check glra_midi/cli.py glra_midi/__init__.py glra_midi/__main__.py
$PY -m unittest discover -s tests -t . -v
