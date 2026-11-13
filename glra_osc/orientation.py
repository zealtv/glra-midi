# SPDX-License-Identifier: GPL-3.0-only

"""The pad held any of four ways: physical control <-> displayed number and grid cell.

Pure. Physical ids are `layout.json`'s names (`key.1`..`key.16`, `enc.1`..`enc.3`,
numbered with the dials along the top edge); a profile stores assignments by
physical id, so changing orientation remaps nothing. Orientation changes only how
the app and `monitor` number, label and draw the controls (docs/config-app.md §6).

Each orientation rotates the pad clockwise from the one before it. With the grid
as `(row, col)`, 0-based, physical `(r, c)` shows at:

    dials-top     (r, c)
    dials-right   (c, 3 - r)
    dials-bottom  (3 - r, 3 - c)
    dials-left    (3 - c, r)

Displayed key numbers count the displayed grid row by row from the top-left (1..16).
Dials count left to right when along the top or bottom edge, top to bottom when
along the left or right edge.

Clockwise stays clockwise: a dial turn's `cw`/`ccw` is physical and untouched here.
Firmware lighting animations run in the vendor's frame whatever the orientation
(config-app.md §6.3); nothing in this module concerns them.
"""

from .profile import DEFAULT_ORIENTATION, ENCODER_COUNT, KEY_COUNT, ORIENTATIONS

__all__ = [
    "DEFAULT_ORIENTATION",
    "ORIENTATIONS",
    "GRID",
    "dial_number",
    "dial_side",
    "display_control",
    "key_cell",
    "key_number",
    "label",
    "physical_dial",
    "physical_key",
    "quarter_turn",
    "turn_cell",
    "unturn_cell",
]

GRID = 4  # keys sit on a 4 x 4 grid

# The edge of the displayed pad the dials sit along.
_DIAL_SIDE = {
    "dials-top": "top",
    "dials-right": "right",
    "dials-bottom": "bottom",
    "dials-left": "left",
}
# Displayed dial D1, D2, D3 -> physical dial number (config-app.md §6.2).
_DIAL_ORDER = {
    "dials-top": (1, 2, 3),
    "dials-right": (1, 2, 3),
    "dials-bottom": (3, 2, 1),
    "dials-left": (3, 2, 1),
}


def _check_orientation(orientation):
    if orientation not in ORIENTATIONS:
        raise ValueError(
            f"orientation: expected one of {', '.join(ORIENTATIONS)}, got {orientation!r}"
        )


def _check_number(what, n, count):
    if isinstance(n, bool) or not isinstance(n, int) or not 1 <= n <= count:
        raise ValueError(f"{what}: expected 1..{count}, got {n!r}")


def _check_cell(row, col):
    if not (0 <= row < GRID and 0 <= col < GRID):
        raise ValueError(f"cell: expected 0..{GRID - 1}, got ({row}, {col})")


def quarter_turn(row, col):
    """A grid cell after one clockwise quarter turn of the pad."""
    return col, GRID - 1 - row


def turn_cell(orientation, row, col):
    """Physical grid cell `(row, col)` -> the cell it occupies in `orientation`."""
    _check_orientation(orientation)
    _check_cell(row, col)
    for _ in range(ORIENTATIONS.index(orientation)):
        row, col = quarter_turn(row, col)
    return row, col


def unturn_cell(orientation, row, col):
    """Displayed cell in `orientation` -> the physical cell (inverse of `turn_cell`)."""
    _check_orientation(orientation)
    _check_cell(row, col)
    for _ in range(-ORIENTATIONS.index(orientation) % 4):
        row, col = quarter_turn(row, col)
    return row, col


# --- keys ---------------------------------------------------------------------------------


def key_cell(orientation, physical):
    """Displayed `(row, col)`, 0-based, of physical key `physical` (1..16)."""
    _check_number("physical key", physical, KEY_COUNT)
    return turn_cell(orientation, (physical - 1) // GRID, (physical - 1) % GRID)


def key_number(orientation, physical):
    """Displayed key number (1..16) of physical key `physical` (1..16)."""
    row, col = key_cell(orientation, physical)
    return row * GRID + col + 1


def physical_key(orientation, number):
    """Physical key (1..16) that shows as displayed key `number`."""
    _check_number("displayed key", number, KEY_COUNT)
    row, col = unturn_cell(orientation, (number - 1) // GRID, (number - 1) % GRID)
    return row * GRID + col + 1


# --- dials --------------------------------------------------------------------------------


def dial_side(orientation):
    """Which edge the dials sit along: `"top"`, `"right"`, `"bottom"` or `"left"`."""
    _check_orientation(orientation)
    return _DIAL_SIDE[orientation]


def dial_number(orientation, physical):
    """Displayed dial number (1..3) of physical dial `physical` (1..3).

    Dials count left to right along the top or bottom edge, top to bottom along
    the left or right edge.
    """
    _check_orientation(orientation)
    _check_number("physical dial", physical, ENCODER_COUNT)
    return _DIAL_ORDER[orientation].index(physical) + 1


def physical_dial(orientation, number):
    """Physical dial (1..3) that shows as displayed dial `number`."""
    _check_orientation(orientation)
    _check_number("displayed dial", number, ENCODER_COUNT)
    return _DIAL_ORDER[orientation][number - 1]


# --- control names ------------------------------------------------------------------------


def _split(control):
    """`"key.13"` -> `("key", 13, "")`; `"enc.2.push"` -> `("enc", 2, "push")`.

    A dial the decoder can't tell apart (`enc.?`) has number `None`.
    """
    parts = control.split(".")
    kind = parts[0]
    if kind not in ("key", "enc") or len(parts) not in (2, 3):
        raise ValueError(f"control: unknown control {control!r}")
    part = parts[2] if len(parts) == 3 else ""
    if kind == "key" and part:
        raise ValueError(f"control: unknown control {control!r}")
    if part not in ("", "push", "turn"):
        raise ValueError(f"control: unknown control {control!r}")
    if parts[1] == "?" and kind == "enc":
        return kind, None, part
    if not parts[1].isdigit():
        raise ValueError(f"control: unknown control {control!r}")
    return kind, int(parts[1]), part


def display_control(orientation, control):
    """Physical control name -> `(kind, displayed number, part)`.

    `"key.13"` in dials-right -> `("key", 1, "")`; `"enc.3.push"` in dials-bottom ->
    `("enc", 1, "push")`. `kind` is `"key"` or `"enc"` (a dial); `part` is `""`,
    `"push"` or `"turn"`. A dial named `enc.?` (the decoder's name while it can't
    tell the dials apart) keeps number `None`. Raises `ValueError` for anything
    that isn't a control.
    """
    _check_orientation(orientation)
    kind, n, part = _split(control)
    if n is None:
        return kind, None, part
    if kind == "key":
        return kind, key_number(orientation, n), part
    return kind, dial_number(orientation, n), part


def label(orientation, control):
    """The app's name for a control: `Key 1`, `Dial 3 push`, `Dial 2 turn`."""
    kind, n, part = display_control(orientation, control)
    name = "Key" if kind == "key" else "Dial"
    text = f"{name} {'?' if n is None else n}"
    return f"{text} {part}" if part else text
