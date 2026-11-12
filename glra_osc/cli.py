# SPDX-License-Identifier: GPL-3.0-only

"""Command line entry point: `--version`, `monitor`, `run` and `unsilence`."""

import argparse
import sys

from . import __version__


def main(argv=None):
    parser = argparse.ArgumentParser(prog="glra-osc", description=__doc__)
    parser.add_argument("--version", action="version", version=f"glra-osc {__version__}")
    sub = parser.add_subparsers(dest="command")
    mon = sub.add_parser("monitor", help="print the pad's decoded control events (read-only)")
    mon.add_argument("--raw", action="store_true", help="also print each raw report as hex")
    typing_help = "run even if the pad can't be silenced (it then types into the focused app)"
    mon.add_argument("--allow-typing", action="store_true", help=typing_help)
    run_p = sub.add_parser("run", help="send the pad's controls as MIDI on a virtual port")
    run_p.add_argument("--config", metavar="FILE", help="mapping file (default: the shipped one)")
    run_p.add_argument(
        "--dry-run", action="store_true", help="print the MIDI instead of sending it"
    )
    run_p.add_argument("--allow-typing", action="store_true", help=typing_help)
    sub.add_parser(
        "unsilence",
        help="remove glra-osc's key-mapping entries from the pad (after a crash or kill -9)",
    )
    args = parser.parse_args(argv)
    if args.command == "monitor":
        from .monitor import run

        return run(raw=args.raw, allow_typing=args.allow_typing)
    if args.command == "run":
        from .mapping import MappingError
        from .runner import run

        try:
            return run(config=args.config, dry_run=args.dry_run, allow_typing=args.allow_typing)
        except MappingError as err:
            print(f"glra-osc: {err}", file=sys.stderr)
            return 2
    if args.command == "unsilence":
        from .decode import load_layout
        from .silence import SilenceError, Silencer

        try:
            removed = Silencer(load_layout()).unsilence()
        except SilenceError as err:
            print(f"glra-osc: {err}", file=sys.stderr)
            return 1
        print(f"removed {removed} entries" if removed else "nothing to remove")
        return 0
    parser.print_help()
    return 0
