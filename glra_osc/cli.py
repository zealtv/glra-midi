# SPDX-License-Identifier: GPL-3.0-only

"""Command line entry point. Placeholder: only `--version` exists so far."""

import argparse

from . import __version__


def main(argv=None):
    parser = argparse.ArgumentParser(prog="glra-osc", description=__doc__)
    parser.add_argument("--version", action="version", version=f"glra-osc {__version__}")
    parser.parse_args(argv)
    parser.print_help()
    return 0
