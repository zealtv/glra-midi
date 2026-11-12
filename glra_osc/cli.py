# SPDX-License-Identifier: GPL-3.0-only

"""Command line entry point: `--version` and `monitor`."""

import argparse

from . import __version__


def main(argv=None):
    parser = argparse.ArgumentParser(prog="glra-osc", description=__doc__)
    parser.add_argument("--version", action="version", version=f"glra-osc {__version__}")
    sub = parser.add_subparsers(dest="command")
    mon = sub.add_parser("monitor", help="print the pad's decoded control events (read-only)")
    mon.add_argument("--raw", action="store_true", help="also print each raw report as hex")
    args = parser.parse_args(argv)
    if args.command == "monitor":
        from .monitor import run

        return run(raw=args.raw)
    parser.print_help()
    return 0
