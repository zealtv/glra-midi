# SPDX-License-Identifier: GPL-3.0-only

"""The configuration app (docs/config-app.md section 4).

`summary.py` is pure and imports without Qt. Everything that needs PySide6 sits behind
`main()`, which imports it on demand, so `glra-osc` itself runs without the `gui` extra.
"""

import sys

__all__ = ["main"]


def main(argv=None):
    """Start the app (`glra-osc-config`, `glra-osc config`, `python -m glra_osc.app`)."""
    try:
        from .gui import main as gui_main

        return gui_main(argv)
    except ImportError as err:
        if err.name and err.name.split(".")[0] in ("PySide6", "shiboken6"):
            print(
                "glra-osc: the configuration app needs PySide6; install it with\n"
                "  pip install 'glra-osc[gui]'",
                file=sys.stderr,
            )
            return 2
        raise
