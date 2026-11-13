# SPDX-License-Identifier: GPL-3.0-only

"""The one internal event type the pad decodes into, and its log-line format."""

import time
from dataclasses import dataclass

ACTIONS = ("down", "up", "cw", "ccw")


@dataclass(frozen=True)
class ControlEvent:
    """One logical control action.

    control: "key.7", "enc.2", "enc.2.push" (a dial is "enc.?" until the
        pad's dials send distinct codes).
    action:  "down"/"up" for keys and dial pushes, "cw"/"ccw" for dial turns.
    t:       seconds on the monotonic clock when the report arrived.
    """

    control: str
    action: str
    t: float


def format_time(wall):
    """`[12:01:03.122]` in local time."""
    ms = round(wall * 1000)
    return f"[{time.strftime('%H:%M:%S', time.localtime(ms // 1000))}.{ms % 1000:03d}]"


def format_event(event, wall=None, orientation=None):
    """`[12:01:03.122] KEY 07 DOWN`.

    With an `orientation` (a profile is in use) the label carries the displayed
    number and the physical id in brackets: `KEY 01 [key.13] DOWN` in dials-right.
    """
    wall = time.time() if wall is None else wall
    kind, _, rest = event.control.partition(".")
    if orientation is not None:
        label = _oriented_label(orientation, event.control)
        if label is not None:
            return f"{format_time(wall)} {label} {event.action.upper()}"
    if kind == "key" and rest.isdigit():
        label = f"KEY {int(rest):02d}"
    elif kind == "enc":
        label = "ENC " + rest.replace(".push", " PUSH")
    else:
        label = event.control.upper()
    return f"{format_time(wall)} {label} {event.action.upper()}"


def _oriented_label(orientation, control):
    """`KEY 01 [key.13]`, `ENC 3 PUSH [enc.1.push]`; None for a name that isn't a control."""
    from .orientation import display_control

    try:
        kind, number, part = display_control(orientation, control)
    except ValueError:
        return None  # e.g. key.unknown:0x65: keep the plain label
    if kind == "key":
        return f"KEY {number:02d} [{control}]"
    text = f"ENC {'?' if number is None else number}"
    return f"{text} {part.upper()} [{control}]" if part else f"{text} [{control}]"
