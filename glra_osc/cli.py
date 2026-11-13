# SPDX-License-Identifier: GPL-3.0-only

"""Command line entry point: `--version`, `monitor`, `run`, `lights`, `config` and `unsilence`."""

import argparse
import sys

from . import __version__


def main(argv=None):
    argv = sys.argv[1:] if argv is None else list(argv)
    if argv[:1] == ["config"]:
        # Everything after `config` belongs to the app (`--demo`, `--help`, ...).
        from .app import main as config_main

        return config_main(argv[1:])
    parser = argparse.ArgumentParser(prog="glra-osc", description=__doc__)
    parser.add_argument("--version", action="version", version=f"glra-osc {__version__}")
    sub = parser.add_subparsers(dest="command")
    mon = sub.add_parser("monitor", help="print the pad's decoded control events (read-only)")
    mon.add_argument("--raw", action="store_true", help="also print each raw report as hex")
    mon.add_argument(
        "--profile",
        metavar="FILE",
        help="number events as displayed in this profile's orientation (physical id in brackets)",
    )
    typing_help = "run even if the pad can't be silenced (it then types into the focused app)"
    mon.add_argument("--allow-typing", action="store_true", help=typing_help)
    run_p = sub.add_parser("run", help="send the pad's controls as MIDI on a virtual port")
    run_p.add_argument(
        "--config",
        metavar="FILE",
        help="play this profile file (default: the profile named in the app folder's `current`)",
    )
    run_p.add_argument(
        "--dry-run",
        action="store_true",
        help="print pad events, layer changes and the MIDI instead of sending it",
    )
    run_p.add_argument("--allow-typing", action="store_true", help=typing_help)
    lights = sub.add_parser(
        "lights",
        help="show the pad's factory RGB mode; with --apply, write the profile's [lighting]",
    )
    lights.add_argument("--profile", metavar="FILE", help="profile file (default: the user's)")
    lights.add_argument(
        "--apply",
        action="store_true",
        help="write the profile's [lighting] to the pad after showing the change and asking "
        "(each write is saved in the pad's flash)",
    )
    sub.add_parser(
        "config",
        help="open the configuration app (needs the `gui` extra); see `glra-osc config --help`",
        add_help=False,
    )
    sub.add_parser(
        "unsilence",
        help="remove glra-osc's key-mapping entries from the pad (after a crash or kill -9)",
    )
    args = parser.parse_args(argv)
    if args.command == "monitor":
        from .monitor import run

        from .profile import ProfileError

        try:
            return run(raw=args.raw, allow_typing=args.allow_typing, profile=args.profile)
        except ProfileError as err:
            print(f"glra-osc: {err}", file=sys.stderr)
            return 2
    if args.command == "run":
        from .profile import ProfileError
        from .runner import run

        try:
            return run(config=args.config, dry_run=args.dry_run, allow_typing=args.allow_typing)
        except ProfileError as err:
            print(f"glra-osc: {err}", file=sys.stderr)
            return 2
    if args.command == "lights":
        from .lighting import lights_command

        return lights_command(profile_path=args.profile, apply_changes=args.apply)
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
