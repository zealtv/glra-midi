# SPDX-License-Identifier: GPL-3.0-only

"""The device panel's logic, without Qt: lighting edits and the dict the QML reads.

`docs/config-app.md` 4.10 and section 5. Every function here returns a new `Lighting` or a
plain value; the controller puts the result into the profile. Nothing in this module touches a
pad: only `Controller.applyLighting` does, on an explicit click.
"""

import colorsys
from dataclasses import replace

from .. import lighting as lights
from ..profile import DEFAULT_BRIGHTNESS, DEFAULT_SPEED, Lighting

NOT_SET = -1  # the selector's "leave the pad's lighting alone" entry: no `[lighting]` section
DEFAULT_COLOR = (0, 255, 255)  # h, s, v for a first "one colour" (the demo profile's)
LEVELS = tuple(range(lights.BRIGHTNESS_RANGE[0], lights.BRIGHTNESS_RANGE[1] + 1))
NO_LIGHTING = "No lighting set in this profile."


def mode_choices():
    """`[{value, label}]` for the selector: "Leave as it is", then the thirteen factory modes."""
    return [{"value": NOT_SET, "label": "Leave as it is"}] + [
        {"value": m.number, "label": m.name} for m in lights.MODES
    ]


def with_mode(current, mode):
    """`current` (a `Lighting` or None) switched to `mode`; `NOT_SET` gives None.

    Brightness and speed carry over; a colour goes when the new mode takes none.
    """
    if mode == NOT_SET:
        return None
    if mode not in lights.MODE_BY_NUMBER:
        raise lights.LightingError(f"mode {mode} doesn't exist (0..{len(lights.MODES) - 1})")
    base = current or Lighting(mode=mode, brightness=DEFAULT_BRIGHTNESS, speed=DEFAULT_SPEED)
    color = base.color if lights.MODE_BY_NUMBER[mode].color else None
    return replace(base, mode=mode, color=color)


def with_level(current, field, value):
    """`current` with `brightness` or `speed` set to `value` (0..4)."""
    if current is None:
        raise lights.LightingError("no lighting is set")
    if field not in ("brightness", "speed"):
        raise lights.LightingError(f"unknown lighting field {field!r}")
    lo, hi = lights.BRIGHTNESS_RANGE if field == "brightness" else lights.SPEED_RANGE
    if type(value) is not int or not lo <= value <= hi:
        raise lights.LightingError(f"{field} must be {lo}..{hi}, got {value!r}")
    return replace(current, **{field: value})


def with_color(current, on):
    """One colour on (the default hue, or the one it had) or off; only for modes that take one."""
    if current is None:
        raise lights.LightingError("no lighting is set")
    if not on:
        return replace(current, color=None)
    if not lights.MODE_BY_NUMBER[current.mode].color:
        raise lights.LightingError(f"{lights.MODE_BY_NUMBER[current.mode].name} takes no colour")
    return replace(current, color=current.color or DEFAULT_COLOR)


def with_hsv(current, index, value):
    """Set one of h, s, v (index 0, 1, 2) to `value` 0..255; turns the colour on if it was off."""
    if current is None or not lights.MODE_BY_NUMBER[current.mode].color:
        raise lights.LightingError("this mode takes no colour")
    if index not in (0, 1, 2) or type(value) is not int or not 0 <= value <= 255:
        raise lights.LightingError(f"colour byte {index} must be 0..255, got {value!r}")
    hsv = list(current.color or DEFAULT_COLOR)
    hsv[index] = value
    return replace(current, color=tuple(hsv))


def swatch(hsv):
    """`#rrggbb` for an `(h, s, v)` of bytes. The pad's hue scale isn't verified; this reads the
    byte as a fraction of the colour wheel, so the swatch approximates what the pad shows."""
    r, g, b = colorsys.hsv_to_rgb(hsv[0] / 255, hsv[1] / 255, hsv[2] / 255)
    return f"#{round(r * 255):02x}{round(g * 255):02x}{round(b * 255):02x}"


def describe_lighting(light):
    """The lighting fields as the QML reads them."""
    modes = mode_choices()
    if light is None:
        return {
            "set": False,
            "mode": NOT_SET,
            "modes": modes,
            "brightness": {"shown": False, "value": 0},
            "speed": {"shown": False, "value": 0},
            "color": {"shown": False, "on": False, "h": 0, "s": 255, "v": 255, "swatch": ""},
            "levels": list(LEVELS),
            "note": NO_LIGHTING,
        }
    mode = lights.MODE_BY_NUMBER.get(light.mode)
    h, s, v = light.color or DEFAULT_COLOR
    return {
        "set": True,
        "mode": light.mode,
        "modes": modes,
        "brightness": {"shown": bool(mode and mode.brightness), "value": light.brightness},
        "speed": {"shown": bool(mode and mode.speed), "value": light.speed},
        "color": {
            "shown": bool(mode and mode.color),
            "on": light.color is not None,
            "h": h,
            "s": s,
            "v": v,
            "swatch": swatch((h, s, v)),
        },
        "levels": list(LEVELS),
        "note": "",
    }


def lighting_problem(light):
    """Why `light` can't be sent to the pad, or `""` (also `""` for None: nothing to send)."""
    if light is None:
        return ""
    try:
        lights.check(light)
    except lights.LightingError as err:
        return str(err)
    return ""
