# SPDX-License-Identifier: GPL-3.0-only

"""Tile text for the pad view: what a control does on the shown layer (docs/config-app.md 4.4).

Pure: no Qt, no I/O. `summarize` gives the two short lines for one event; `tile_info` gives
everything a tile shows (state, badge, both lines) for a control on a tab.

Note names put C1 at 36, so middle C (60) reads C3, the convention Ableton Live and Yamaha
use. The inspector shows the number beside the name, so nothing hides.
"""

from ..profile import (
    CcAbsolute,
    CcMomentary,
    CcRelative,
    CcSet,
    CcStep,
    NO_LAYER,
    LayerDec,
    LayerInc,
    LayerSet,
    Note,
    control_shape,
)

__all__ = ["BADGE_GLOBAL", "BADGE_LAYER_KEY", "BADGE_PER_LAYER", "note_name", "summarize", "tile_info"]

BADGE_GLOBAL = "G"
BADGE_LAYER_KEY = "🔒"
BADGE_PER_LAYER = "≠"  # the Global tab's tile for a control that differs by layer
_NOTES = ("C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B")
_ENCODING = {"twos-complement": "2's", "binary-offset": "offset", "signed-bit": "sign"}
MINUS = "\N{MINUS SIGN}"


def note_name(number):
    """`36` -> `C1`, `61` -> `C#3` (C1 = 36)."""
    return f"{_NOTES[number % 12]}{number // 12 - 2}"


def _channel_text(event, default_channel):
    channel = getattr(event, "channel", None)
    if channel is None or channel == default_channel:
        return ""
    return f"ch {channel}"


def _join(*parts):
    return " · ".join(p for p in parts if p)


def summarize(event, default_channel=1, layer_names=(), note_names=True):
    """`(line 1, line 2)` for one event. The channel shows (as `ch 10`, at the end of line 2)
    only when it differs from `default_channel`. `layer_names` is the profile's, for the
    layer name on a `layer-set` tile."""
    ch = _channel_text(event, default_channel)
    if isinstance(event, Note):
        name = note_name(event.note) if note_names else str(event.note)
        first = f"Note {name}"
        if event.mode == "latch":
            return first, _join("latch", f"vel {event.velocity}", ch)
        return first, _join(f"vel {event.velocity}", ch)
    if isinstance(event, CcMomentary):
        first = f"CC{event.cc} {event.low}↔{event.high}"
        glide = ""
        if event.rise_ms or event.fall_ms:
            glide = f"↑{event.rise_ms} ↓{event.fall_ms} ms {event.curve}"
        return first, _join(glide, "latch" if event.mode == "latch" else "", ch)
    if isinstance(event, CcSet):
        return f"CC{event.cc} = {event.value}", ch
    if isinstance(event, CcStep):
        sign = "+" if event.step > 0 else MINUS
        return (
            f"CC{event.cc} {sign}{abs(event.step)}",
            _join(f"{event.ease_ms} ms" if event.ease_ms else "", ch),
        )
    if isinstance(event, LayerSet):
        if event.layer == NO_LAYER:
            return "→ L?", "removed"
        name = layer_names[event.layer - 1] if 0 < event.layer <= len(layer_names) else ""
        return f"→ L{event.layer}", name
    if isinstance(event, LayerInc):
        return "L+1 ▶", "wraps"
    if isinstance(event, LayerDec):
        return f"◀ L{MINUS}1", "wraps"
    if isinstance(event, CcRelative):
        return f"CC{event.cc} rel", _join(_ENCODING[event.encoding], ch)
    if isinstance(event, CcAbsolute):
        return f"CC{event.cc} abs", _join(f"step {event.step}", ch)
    raise TypeError(f"not an event: {event!r}")


def tile_info(profile, control, tab, note_names=True):
    """What the tile of physical control `control` shows on `tab` (None = the Global tab,
    else a 1-based layer). A dict:

    * `state`: `"empty"`, `"layer"` (an event on this layer), `"global"`, `"layer-key"` or
      `"per-layer"` (the Global tab's dimmed tile for a control that differs by layer);
    * `badge`: `"G"`, `"🔒"`, `"≠"` (Global tab, per-layer control) or `""`: state shows by badge as well as colour;
    * `line1`, `line2`: the text;
    * `layers_used`, `layers_total`: for `"per-layer"`, how many layers hold an event.
    """
    value = profile.controls.get(control)
    shape = control_shape(value)
    info = {"state": "empty", "badge": "", "line1": "—", "line2": "", "layers_used": 0}
    info["layers_total"] = profile.layer_count
    if shape == "none":
        return info
    if shape == "per-layer":
        if tab is None:
            used = len(value.events)
            info.update(
                state="per-layer", badge=BADGE_PER_LAYER, line1="per layer", layers_used=used
            )
            info["line2"] = f"{used} of {profile.layer_count}"
            return info
        value = value.get(tab)
        if value is None:
            return info
        state, badge = "layer", ""
    elif shape == "layer-key":
        state, badge = "layer-key", BADGE_LAYER_KEY
    else:
        state, badge = "global", BADGE_GLOBAL
    line1, line2 = summarize(value, profile.channel, profile.layer_names, note_names)
    info.update(state=state, badge=badge, line1=line1, line2=line2)
    return info

