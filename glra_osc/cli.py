# SPDX-License-Identifier: GPL-3.0-only

"""Command line entry point: `--version`, `monitor` and `run`."""

import argparse
import sys

from . import __version__


def main(argv=None):
    parser = argparse.ArgumentParser(prog="glra-osc", description=__doc__)
    parser.add_argument("--version", action="version", version=f"glra-osc {__version__}")
    sub = parser.add_subparsers(dest="command")
    mon = sub.add_parser("monitor", help="print the pad's decoded control events (read-only)")
    mon.add_argument("--raw", action="store_true", help="also print each raw report as hex")
    run_p = sub.add_parser("run", help="send the pad's controls as MIDI on a virtual port")
    run_p.add_argument("--config", metavar="FILE", help="mapping file (default: the shipped one)")
    run_p.add_argument(
        "--dry-run", action="store_true", help="print the MIDI instead of sending it"
    )
    args = parser.parse_args(argv)
    if args.command == "monitor":
        from .monitor import run

        return run(raw=args.raw)
    if args.command == "run":
        from .mapping import MappingError
        from .runner import run

        try:
            return run(config=args.config, dry_run=args.dry_run)
        except MappingError as err:
            print(f"glra-osc: {err}", file=sys.stderr)
            return 2
    parser.print_help()
    return 0
