#!/bin/sh
# Lint + tests. Run from anywhere; uses the repo's .venv.
set -e
cd "$(dirname "$0")"
PY=.venv/bin/python
$PY -m ruff check glra_osc tests
$PY -m ruff format --check glra_osc/cli.py glra_osc/__init__.py glra_osc/__main__.py
$PY -m unittest discover -s tests -t . -v
