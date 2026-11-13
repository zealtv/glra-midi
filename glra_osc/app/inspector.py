# SPDX-License-Identifier: GPL-3.0-only

"""What the inspector shows and how a typed value becomes an event (docs/config-app.md 4.5, 4.6).

Pure: no Qt, no I/O. `describe` turns (profile, control, tab, drafts) into the plain dict the
QML reads; `apply_field` and `default_event` build the new event an edit hands to
`profile.set_event`. A typed value is checked by `profile.event_from_fields`, the parser's own
rules, so the field says what the file would say (path prefix dropped: the field label is the
path).
"""

import re

from .. import profile as prof
from .summary import note_name, summarize

PRESS_KINDS = (
    ("note", "Note"),
    ("cc-momentary", "CC momentary"),
    ("cc-set", "CC set value"),
    ("cc-step", "CC inc / dec"),
)
TURN_KINDS = (("cc-relative", "CC relative"), ("cc-absolute", "CC absolute"))
LAYER_KEY_CHOICES = (("layer-set", "Set"), ("layer-inc", "Next"), ("layer-dec", "Previous"))
LAYER_KEY_KINDS = tuple(k for k, _ in LAYER_KEY_CHOICES)

DEFAULT_CC = 16
_INT = re.compile(r"[+-]?\d+")
_LAYER_KEYS = (prof.LayerSet, prof.LayerInc, prof.LayerDec)


def is_layer_key(action):
    return isinstance(action, _LAYER_KEYS)


def default_event(kind, previous=None):
    """A fresh event of `kind`, keeping the `cc` and `channel` of `previous` when it had them."""
    cc = getattr(previous, "cc", DEFAULT_CC)
    channel = getattr(previous, "channel", None)
    if kind == "note":
        return prof.Note(note=36, channel=channel)
    if kind == "cc-momentary":
        return prof.CcMomentary(cc=cc, channel=channel)
    if kind == "cc-set":
        return prof.CcSet(cc=cc, value=64, channel=channel)
    if kind == "cc-step":
        return prof.CcStep(cc=cc, step=1, channel=channel)
    if kind == "cc-relative":
        return prof.CcRelative(cc=cc, channel=channel)
    if kind == "cc-absolute":
        return prof.CcAbsolute(cc=cc, channel=channel)
    raise prof.ProfileError(f"kind: {kind!r} isn't an event kind")


def _strip_path(message):
    return message.partition(": ")[2] or message


def _parse_int(text, spec):
    """The value a field's text means: an int, None (optional field left empty or `default`),
    or the raw text when it isn't a number (the parser then says why)."""
    text = text.strip()
    if spec["default"] is None and not spec["required"] and text in ("", "default"):
        return None
    return int(text) if _INT.fullmatch(text) else text


def apply_field(event, key, text):
    """`event` with field `key` set from `text`. Raises `ProfileError` whose message is the
    parser's, without the key path. `size` and `direction` are the two halves of a CC inc/dec
    `step`."""
    fields = prof.event_fields(event)
    if event.kind == "cc-step" and key in ("size", "direction"):
        if key == "size":
            size = _parse_int(str(text), {"default": 0, "required": True})
            if not isinstance(size, int) or not 1 <= size <= 127:
                raise prof.ProfileError(f"expected an integer 1..127, got {size!r}")
            fields["step"] = size if fields["step"] > 0 else -size
        else:
            if text not in ("inc", "dec"):
                raise prof.ProfileError(f"expected inc or dec, got {text!r}")
            fields["step"] = abs(fields["step"]) * (1 if text == "inc" else -1)
    else:
        specs = {s["key"]: s for s in prof.event_field_specs(event.kind)}
        if key not in specs:
            raise prof.ProfileError(f"not a field of {event.kind}")
        spec = specs[key]
        fields[key] = _parse_int(str(text), spec) if spec["type"] == "int" else text
    try:
        return prof.event_from_fields(event.kind, fields, path="x")
    except prof.ProfileError as err:
        raise prof.ProfileError(_strip_path(str(err))) from None


def _field_entries(event, drafts):
    """`{key: {text, error, range}}` for the event's fields as the inspector lists them."""
    values = prof.event_fields(event)
    entries = {}
    for spec in prof.event_field_specs(event.kind):
        key = spec["key"]
        if event.kind == "cc-step" and key == "step":
            continue
        value = values[key]
        text = "default" if value is None and key == "channel" else "" if value is None else str(value)
        rng = f"{spec['lo']}..{spec['hi']}" if spec["type"] == "int" else ""
        entries[key] = {"text": text, "error": "", "range": rng}
    if event.kind == "cc-step":
        step = values["step"]
        entries["size"] = {"text": str(abs(step)), "error": "", "range": "1..127"}
        entries["direction"] = {"text": "inc" if step > 0 else "dec", "error": "", "range": ""}
    for key, (text, error) in drafts.items():
        if key in entries:
            entries[key].update(text=text, error=error)
    return entries


def _list_layers(layers):
    names = [str(n) for n in layers]
    if len(names) == 1:
        return f"layer {names[0]}"
    return "layers " + ", ".join(names[:-1]) + " and " + names[-1]


def discard_text(label, discarded, kept_layer=None):
    """The question put to Bob before an edit throws events away (design 4.6)."""
    layers = [d.layer for d in discarded if d.layer is not None]
    if layers:
        have = f"{label} has its own events on {_list_layers(layers)}."
        if kept_layer is not None:
            return f"{have} Make layer {kept_layer}'s event apply to all layers and discard those?"
        return f"{have} Make it a layer key and discard them?"
    return f"{label} holds an event that applies on every layer. Make it a layer key and discard it?"


def describe(profile, control, tab, drafts=None, note_names=True):
    """Everything the inspector's fields need for `control` shown on `tab` (None or 0: the
    Global tab). Keys:

    * `turn`: a dial turn (else a press);
    * `mode`: `"event"`, `"layer-key"`, `"none"`, or `"each"` (a per-layer control seen from the
      Global tab: nothing to edit here, pick a layer);
    * `action`: for presses `"event"` | `"layer"` | `"none"`; for turns the event kind or `"none"`;
    * `actions`: `[{value, label}]` the choices for it;
    * `applies`: `"layer"` | `"global"` (events only); `appliesText`: its words;
    * `kind`, `kinds`: the event kind and the kinds this control takes;
    * `fields`, `noteName`: see `_field_entries`;
    * `layerKey`: `{kind, layer}` for layer keys; `layerChoices`: the layers a Set can name;
    * `alsoOn`: `[{layer, text}]` for a per-layer control's other layers;
    * `defaultChannel`: the profile's `[midi] channel`.
    """
    tab = tab or None
    drafts = drafts or {}
    turn = control in prof.TURN_CONTROLS
    value = profile.controls.get(control)
    shape = prof.control_shape(value)
    kinds = TURN_KINDS if turn else PRESS_KINDS
    out = {
        "turn": turn,
        "mode": "none",
        "action": "none",
        "actions": [{"value": k, "label": label} for k, label in kinds]
        if turn
        else [
            {"value": "event", "label": "Event"},
            {"value": "layer", "label": "Layer"},
            {"value": "none", "label": "None"},
        ],
        "applies": "layer",
        "appliesText": "",
        "kind": "",
        "kinds": [{"value": k, "label": label} for k, label in kinds],
        "fields": {},
        "noteName": "",
        "layerKey": {"kind": "layer-inc", "layer": tab or 1},
        "layerChoices": list(range(1, profile.layer_count + 1)),
        "alsoOn": [],
        "layersUsed": "",
        "defaultChannel": profile.channel,
    }
    if shape == "per-layer" and tab is None:
        used = [n for n, _ in value.events]
        out.update(mode="each", applies="each", layersUsed=_list_layers(used).capitalize())
        out["appliesText"] = "Different on each layer"
        return out
    action = value if shape != "per-layer" else value.get(tab)
    if action is None:
        out["applies"] = "global" if tab is None else "layer"
    elif is_layer_key(action):
        out.update(mode="layer-key", action="layer", applies="global")
        out["layerKey"] = {
            "kind": action.kind,
            "layer": getattr(action, "layer", tab or 1),
        }
        out["appliesText"] = "Works the same on every layer"
        return out
    else:
        out.update(
            mode="event",
            action=action.kind if turn else "event",
            kind=action.kind,
            applies="global" if shape == "global" else "layer",
        )
        out["appliesText"] = "All layers" if shape == "global" else "This layer"
        out["fields"] = _field_entries(action, drafts)
        if isinstance(action, prof.Note):
            out["noteName"] = note_name(action.note) if note_names else ""
    if shape == "per-layer":
        for n in range(1, profile.layer_count + 1):
            if n == tab:
                continue
            other = value.get(n)
            text = summarize(other, profile.channel, profile.layer_names, note_names)[0] if other else "—"
            out["alsoOn"].append({"layer": n, "text": f"L{n} {text}"})
    return out
