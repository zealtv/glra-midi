#!/bin/sh
# Render a named app state to a PNG, offscreen: tools/app-capture.sh <state> <out.png> [--dark]
# States are listed by `python -m glra_osc.app --help`. Needs the `gui` extra.
set -e
cd "$(dirname "$0")/.."
[ $# -ge 2 ] || { echo "usage: $0 <state> <out.png> [--dark]" >&2; exit 2; }
state=$1
out=$2
shift 2
QT_QPA_PLATFORM=offscreen QT_QUICK_BACKEND=software \
    .venv/bin/python -m glra_osc.app --demo --capture "$state" --out "$out" "$@"
