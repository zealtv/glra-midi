# SPDX-License-Identifier: GPL-3.0-only

"""The profile: layers, events, lighting and orientation, as one TOML file.

A profile is what the configuration app edits and `glra-osc run` plays; the format
is specified in `docs/config-app.md` section 2 and documented in
`default_profile.toml`. This module is pure: no I/O beyond reading and writing the
file, no MIDI, no device.

Shape
-----
Every control (`key.1`..`key.16`, `enc.1.push`..`enc.3.push`, `enc.1.turn`..
`enc.3.turn`; names are *physical*, the file never changes with orientation) holds
exactly one of three things, and the types below make that so:

* a **global** event (the same on every layer), or a **layer key** (`LayerSet`,
  `LayerInc`, `LayerDec`; global by construction): the event object itself;
* **per-layer** events: a `PerLayer`, holding an event per layer it uses.

There is no fall-through from a layer to a global event (Bob, 2026-11-13).

`parse_profile` / `load_profile` validate text into the frozen dataclasses and raise
`ProfileError`, whose message starts with the key path (as `mapping.py` does for
`MappingError`). `validate` does the same for a `Profile` built in code (the edit
helpers can leave a profile with problems, such as a layer key that points past the
last layer after a layer is removed) and returns every problem. `dump_profile` writes a
file that parses back to an equal profile.

A file without `version` is an error: old mapping files no longer load (Bob, 2026-11-13:
"i don't care about todays mapping files, we can hard break").
"""

import os
import re
import stat
import tempfile
import tomllib
from dataclasses import dataclass, field, replace
from importlib import resources
from pathlib import Path
from typing import ClassVar

import tomli_w

PROFILE_VERSION = 1
# Application Support directory name. One constant, so the glra-midi rename touches one
# line (docs/config-app.md section 2, Q9).
APP_DIR_NAME = "glra-osc"
PROFILE_FILE_NAME = "profile.toml"

KEY_COUNT = 16
ENCODER_COUNT = 3
MIN_LAYERS, MAX_LAYERS, DEFAULT_LAYERS = 1, 8, 4
DEFAULT_PORT = "GLRA K16"
DEFAULT_CHANNEL = 1
ORIENTATIONS = ("dials-top", "dials-right", "dials-bottom", "dials-left")
DEFAULT_ORIENTATION = "dials-top"
BUTTON_MODES = ("momentary", "latch")
CURVES = ("linear", "ease-in", "ease-out", "ease-in-out")
RELATIVE_ENCODINGS = ("twos-complement", "binary-offset", "signed-bit")

# Factory RGB modes the profile may name (docs/config-app.md section 5.1). Which of them
# take a fixed colour is inferred, not verified per mode; `lighting-modes` may take over
# this table and the tour checks it (Q6).
LIGHTING_MODES = range(0, 13)
LIGHTING_COLOR_MODES = frozenset({1, 2, 4, 5, 6, 7, 11})
DEFAULT_BRIGHTNESS = 4
DEFAULT_SPEED = 2


class ProfileError(ValueError):
    """The profile is unreadable, invalid or can't be edited that way; the message names the key."""


# --- events -------------------------------------------------------------------------------
# Field names are the TOML keys with "-" as "_". `channel` None means `[midi] channel`.


@dataclass(frozen=True)
class Note:
    kind: ClassVar[str] = "note"
    note: int
    velocity: int = 127
    mode: str = "momentary"
    channel: int | None = None


@dataclass(frozen=True)
class CcMomentary:
    kind: ClassVar[str] = "cc-momentary"
    cc: int
    low: int = 0
    high: int = 127
    ease_ms: int = 0
    curve: str = "linear"
    mode: str = "momentary"
    channel: int | None = None


@dataclass(frozen=True)
class CcSet:
    kind: ClassVar[str] = "cc-set"
    cc: int
    value: int
    channel: int | None = None


@dataclass(frozen=True)
class CcStep:
    kind: ClassVar[str] = "cc-step"
    cc: int
    step: int  # sign is the direction; never 0
    ease_ms: int = 0
    curve: str = "linear"
    channel: int | None = None


@dataclass(frozen=True)
class LayerSet:
    kind: ClassVar[str] = "layer-set"
    layer: int


@dataclass(frozen=True)
class LayerInc:
    kind: ClassVar[str] = "layer-inc"


@dataclass(frozen=True)
class LayerDec:
    kind: ClassVar[str] = "layer-dec"


@dataclass(frozen=True)
class CcRelative:
    kind: ClassVar[str] = "cc-relative"
    cc: int
    encoding: str = "twos-complement"
    channel: int | None = None


@dataclass(frozen=True)
class CcAbsolute:
    kind: ClassVar[str] = "cc-absolute"
    cc: int
    step: int = 1
    initial: int | None = None
    channel: int | None = None


PressEvent = Note | CcMomentary | CcSet | CcStep
LayerKey = LayerSet | LayerInc | LayerDec
TurnEvent = CcRelative | CcAbsolute
Action = PressEvent | LayerKey | TurnEvent  # what a global control can hold


@dataclass(frozen=True)
class PerLayer:
    """Events on some layers; `events` is ((layer, event), ...) ascending by layer."""

    events: tuple[tuple[int, PressEvent | TurnEvent], ...]

    @classmethod
    def of(cls, mapping):
        return cls(tuple(sorted(mapping.items())))

    def as_dict(self):
        return dict(self.events)

    def get(self, layer):
        return self.as_dict().get(layer)


Control = Action | PerLayer


@dataclass(frozen=True)
class Lighting:
    mode: int
    brightness: int = DEFAULT_BRIGHTNESS
    speed: int = DEFAULT_SPEED
    color: tuple[int, int, int] | None = None  # fixed hue h, s, v (0..255)


PRESS_CONTROLS = tuple(f"key.{n}" for n in range(1, KEY_COUNT + 1)) + tuple(
    f"enc.{n}.push" for n in range(1, ENCODER_COUNT + 1)
)
TURN_CONTROLS = tuple(f"enc.{n}.turn" for n in range(1, ENCODER_COUNT + 1))
# Canonical order, as the file writes them: keys, then each dial's push before its turn.
CONTROL_NAMES = tuple(f"key.{n}" for n in range(1, KEY_COUNT + 1)) + tuple(
    f"enc.{n}.{part}" for n in range(1, ENCODER_COUNT + 1) for part in ("push", "turn")
)


@dataclass(frozen=True)
class Profile:
    """Treat `controls` as read-only; the edit helpers return new profiles."""

    port: str = DEFAULT_PORT
    channel: int = DEFAULT_CHANNEL
    orientation: str = DEFAULT_ORIENTATION
    layer_count: int = DEFAULT_LAYERS
    layer_names: tuple[str, ...] = ("",) * DEFAULT_LAYERS  # always `layer_count` long
    lighting: Lighting | None = None
    controls: dict[str, Control] = field(default_factory=dict)

    @property
    def midi_channel(self):
        """The default channel as the 0..15 value that goes into a MIDI status byte."""
        return self.channel - 1

    def action(self, name, layer):
        """What control `name` does on `layer` (1-based): an event, a layer key or None."""
        control = self.controls.get(name)
        if isinstance(control, PerLayer):
            return control.get(layer)
        return control


def control_shape(control):
    """"none" | "global" | "per-layer" | "layer-key" for a control value (None = absent)."""
    if control is None:
        return "none"
    if isinstance(control, PerLayer):
        return "per-layer"
    if isinstance(control, (LayerSet, LayerInc, LayerDec)):
        return "layer-key"
    return "global"


# --- field specs: one table drives parsing, writing and edit-time checking ----------------

_REQUIRED = object()


@dataclass(frozen=True)
class _Int:
    key: str
    lo: int
    hi: int
    default: object = _REQUIRED
    nonzero: bool = False

    @property
    def attr(self):
        return self.key.replace("-", "_")


@dataclass(frozen=True)
class _Choice:
    key: str
    choices: tuple
    default: object = _REQUIRED

    @property
    def attr(self):
        return self.key.replace("-", "_")


_CC = _Int("cc", 0, 127)
_CHANNEL = _Int("channel", 1, 16, default=None)
_EASE = _Int("ease-ms", 0, 10000, default=0)
_CURVE = _Choice("curve", CURVES, default="linear")
_MODE = _Choice("mode", BUTTON_MODES, default="momentary")

EVENT_CLASSES = {
    cls.kind: cls
    for cls in (
        Note,
        CcMomentary,
        CcSet,
        CcStep,
        LayerSet,
        LayerInc,
        LayerDec,
        CcRelative,
        CcAbsolute,
    )
}
_SPECS = {
    "note": (_Int("note", 0, 127), _Int("velocity", 1, 127, default=127), _MODE, _CHANNEL),
    "cc-momentary": (
        _CC,
        _Int("low", 0, 127, default=0),
        _Int("high", 0, 127, default=127),
        _EASE,
        _CURVE,
        _MODE,
        _CHANNEL,
    ),
    "cc-set": (_CC, _Int("value", 0, 127), _CHANNEL),
    "cc-step": (_CC, _Int("step", -127, 127, nonzero=True), _EASE, _CURVE, _CHANNEL),
    # 1..MAX_LAYERS here; the check against `[layers] count` is a cross-control check.
    "layer-set": (_Int("layer", MIN_LAYERS, MAX_LAYERS),),
    "layer-inc": (),
    "layer-dec": (),
    "cc-relative": (
        _CC,
        _Choice("encoding", RELATIVE_ENCODINGS, default="twos-complement"),
        _CHANNEL,
    ),
    "cc-absolute": (_CC, _Int("step", 1, 127, default=1), _Int("initial", 0, 127, default=None), _CHANNEL),
}
PRESS_KINDS = ("note", "cc-momentary", "cc-set", "cc-step")
LAYER_KINDS = ("layer-set", "layer-inc", "layer-dec")
TURN_KINDS = ("cc-relative", "cc-absolute")


# --- paths --------------------------------------------------------------------------------


def default_profile_path():
    """The shipped default profile (read-only package data)."""
    return Path(str(resources.files("glra_osc").joinpath("default_profile.toml")))


def user_profile_path(home=None):
    """Where the app and `glra-osc run` keep the user's profile."""
    home = Path.home() if home is None else Path(home)
    return home / "Library" / "Application Support" / APP_DIR_NAME / PROFILE_FILE_NAME


# --- parsing; every message starts with the key path --------------------------------------


def _table(value, path):
    if not isinstance(value, dict):
        raise ProfileError(f"{path}: expected a table, got {value!r}")
    return value


def _check_keys(table, allowed, path):
    for name in table:
        if name not in allowed:
            where = f"{path}.{name}" if path else name
            raise ProfileError(f"{where}: unknown key (allowed here: {', '.join(allowed)})")


def _is_int(value):
    return isinstance(value, int) and not isinstance(value, bool)


def _int(value, where, lo, hi):
    if not _is_int(value) or not lo <= value <= hi:
        raise ProfileError(f"{where}: expected an integer {lo}..{hi}, got {value!r}")
    return value


def _field(table, spec, path):
    """The value of one spec'd field of `table`, or its default."""
    where = f"{path}.{spec.key}"
    if spec.key not in table:
        if spec.default is _REQUIRED:
            raise ProfileError(f"{where}: required")
        return spec.default
    value = table[spec.key]
    if isinstance(spec, _Choice):
        if value not in spec.choices:
            raise ProfileError(f"{where}: expected one of {', '.join(spec.choices)}, got {value!r}")
        return value
    _int(value, where, spec.lo, spec.hi)
    if spec.nonzero and value == 0:
        raise ProfileError(f"{where}: expected a non-zero integer {spec.lo}..{spec.hi}, got 0")
    return value


def _parse_event(table, path, kinds, layer_key_hint=None):
    """An event from its table; `kinds` are the kinds this place accepts."""
    table = _table(table, path)
    if "kind" not in table:
        raise ProfileError(f"{path}.kind: required")
    kind = table["kind"]
    if layer_key_hint and kind in LAYER_KINDS and kind not in kinds:
        raise ProfileError(f"{path}: layer keys are global; move it to [{layer_key_hint}]")
    if kind not in kinds:
        raise ProfileError(f"{path}.kind: expected one of {', '.join(kinds)}, got {kind!r}")
    specs = _SPECS[kind]
    _check_keys(table, ("kind",) + tuple(s.key for s in specs), path)
    values = {spec.attr: _field(table, spec, path) for spec in specs}
    return EVENT_CLASSES[kind](**values)


def _parse_control(table, name, count):
    """One control's table: a global event or layer key, or per-layer events."""
    turn = name in TURN_CONTROLS
    table = _table(table, name)
    if "layers" in table:
        others = [k for k in table if k != "layers"]
        if others:
            if table.get("kind") in LAYER_KINDS:
                raise ProfileError(f"{name}: a layer key can't also have per-layer events")
            raise ProfileError(
                f"{name}: global and per-layer events exclude each other "
                f"(found {', '.join(others)} beside layers); use `kind` or `layers.<n>`, not both"
            )
        layers = _table(table["layers"], f"{name}.layers")
        if not layers:
            raise ProfileError(f"{name}.layers: no layers given; leave the control out instead")
        kinds = TURN_KINDS if turn else PRESS_KINDS
        events = {}
        for lname, sub in layers.items():
            if not (lname.isascii() and lname.isdigit() and MIN_LAYERS <= int(lname) <= count):
                raise ProfileError(f"{name}.layers.{lname}: layer doesn't exist (count = {count})")
            hint = None if turn else name
            events[int(lname)] = _parse_event(sub, f"{name}.layers.{lname}", kinds, hint)
        return PerLayer.of(events)
    if "kind" not in table:
        raise ProfileError(
            f"{name}: needs `kind` (one event on every layer) or `layers.<n>` tables "
            "(one per layer); leave the control out to do nothing"
        )
    return _parse_event(table, name, TURN_KINDS if turn else PRESS_KINDS + LAYER_KINDS)


def _parse_port_channel(data):
    midi = _table(data.get("midi", {}), "midi")
    _check_keys(midi, ("port", "channel"), "midi")
    port = midi.get("port", DEFAULT_PORT)
    if not isinstance(port, str) or not port.strip():
        raise ProfileError(f"midi.port: expected a non-empty string, got {port!r}")
    channel = DEFAULT_CHANNEL
    if "channel" in midi:
        channel = _int(midi["channel"], "midi.channel", 1, 16)
    return port, channel


def _parse_orientation(data):
    pad = _table(data.get("pad", {}), "pad")
    _check_keys(pad, ("orientation",), "pad")
    value = pad.get("orientation", DEFAULT_ORIENTATION)
    if value not in ORIENTATIONS:
        raise ProfileError(f"pad.orientation: expected one of {', '.join(ORIENTATIONS)}, got {value!r}")
    return value


def _parse_layers(data):
    layers = _table(data.get("layers", {}), "layers")
    _check_keys(layers, ("count", "names"), "layers")
    count = DEFAULT_LAYERS
    if "count" in layers:
        count = _int(layers["count"], "layers.count", MIN_LAYERS, MAX_LAYERS)
    names = layers.get("names", [])
    if (
        not isinstance(names, list)
        or len(names) > count
        or not all(isinstance(n, str) for n in names)
    ):
        raise ProfileError(f"layers.names: expected a list of up to {count} strings, got {names!r}")
    return count, tuple(names) + ("",) * (count - len(names))


def _parse_lighting(data):
    if "lighting" not in data:
        return None
    table = _table(data["lighting"], "lighting")
    _check_keys(table, ("mode", "brightness", "speed", "color"), "lighting")
    if "mode" not in table:
        raise ProfileError("lighting.mode: required")
    mode = _int(table["mode"], "lighting.mode", LIGHTING_MODES.start, LIGHTING_MODES.stop - 1)
    brightness = DEFAULT_BRIGHTNESS
    if "brightness" in table:
        brightness = _int(table["brightness"], "lighting.brightness", 0, 4)
    speed = DEFAULT_SPEED
    if "speed" in table:
        speed = _int(table["speed"], "lighting.speed", 0, 4)
    color = None
    if "color" in table:
        raw = table["color"]
        if not isinstance(raw, list) or len(raw) != 3:
            raise ProfileError(f"lighting.color: expected [hue, saturation, value], got {raw!r}")
        color = tuple(_int(v, "lighting.color", 0, 255) for v in raw)
        if mode not in LIGHTING_COLOR_MODES:
            raise ProfileError(f"lighting.color: mode {mode} doesn't take a single colour")
    return Lighting(mode=mode, brightness=brightness, speed=speed, color=color)


def _control_tables(data):
    """Yield (control name, table) for every control present in the file's key/enc tables."""
    for n, sub in _numbered(data.get("key", {}), KEY_COUNT, "key"):
        yield f"key.{n}", sub
    for n, sub in _numbered(data.get("enc", {}), ENCODER_COUNT, "enc"):
        path = f"enc.{n}"
        sub = _table(sub, path)
        _check_keys(sub, ("push", "turn"), path)
        for part in ("push", "turn"):
            if part in sub:
                yield f"{path}.{part}", sub[part]


def _numbered(table, count, path):
    table = _table(table, path)
    for name, sub in table.items():
        if not (name.isascii() and name.isdigit() and 1 <= int(name) <= count):
            raise ProfileError(f"{path}.{name}: unknown control (expected 1..{count})")
        yield int(name), sub


def _build(data):
    if "version" not in data:
        raise ProfileError(
            f"version: required; a profile starts with `version = {PROFILE_VERSION}` "
            "(old mapping files no longer load)"
        )
    _check_keys(data, ("version", "midi", "pad", "layers", "lighting", "key", "enc"), "")
    version = data["version"]
    if version != PROFILE_VERSION or isinstance(version, bool):
        raise ProfileError(
            f"version: this glra-osc reads version {PROFILE_VERSION}, got {version!r}"
        )
    port, channel = _parse_port_channel(data)
    orientation = _parse_orientation(data)
    count, names = _parse_layers(data)
    lighting = _parse_lighting(data)
    controls = {name: _parse_control(sub, name, count) for name, sub in _control_tables(data)}
    profile = Profile(
        port=port,
        channel=channel,
        orientation=orientation,
        layer_count=count,
        layer_names=names,
        lighting=lighting,
        controls=_in_canonical_order(controls),
    )
    problems = _cross_check(profile)
    if problems:
        raise ProfileError(problems[0].message)
    return profile


def parse_profile(text, source="<profile>"):
    """Validate profile text into a `Profile`."""
    try:
        data = tomllib.loads(text)
    except tomllib.TOMLDecodeError as err:
        raise ProfileError(f"{source}: not valid TOML: {err}") from err
    try:
        return _build(data)
    except ProfileError as err:
        raise ProfileError(f"{source}: {err}") from None


def load_profile(path=None):
    """Load and validate a profile file; with no path, the shipped default."""
    path = default_profile_path() if path is None else Path(path)
    try:
        text = path.read_text(encoding="utf-8")
    except OSError as err:
        raise ProfileError(f"{path}: cannot read profile file: {err.strerror or err}") from err
    return parse_profile(text, source=str(path))


def _in_canonical_order(controls):
    rank = {name: i for i, name in enumerate(CONTROL_NAMES)}
    return dict(sorted(controls.items(), key=lambda item: rank.get(item[0], len(rank))))


# --- validation of a profile built in code ------------------------------------------------


@dataclass(frozen=True)
class Problem:
    """One thing wrong with a profile; `message` starts with the key path."""

    control: str | None  # the control it concerns, when there is one
    message: str


def validate(profile):
    """Every problem with `profile` (empty list: fine). Same rules, same words as parsing."""
    problems = []
    data = _profile_data(profile)
    for step in (_parse_port_channel, _parse_orientation, _parse_layers, _parse_lighting):
        try:
            step(data)
        except ProfileError as err:
            problems.append(Problem(None, str(err)))
    for name, control in profile.controls.items():
        if name not in CONTROL_NAMES:
            problems.append(Problem(name, f"{name}: unknown control"))
            continue
        try:
            _parse_control(_control_data(control), name, profile.layer_count)
        except ProfileError as err:
            problems.append(Problem(name, str(err)))
    if len(profile.layer_names) != profile.layer_count:
        problems.append(
            Problem(
                None, f"layers.names: expected {profile.layer_count} names, got {len(profile.layer_names)}"
            )
        )
    problems.extend(_cross_check(profile))
    return problems


def _each_action(profile):
    """Yield (path, control name, layer or None, action) for every event, in canonical order."""
    for name in CONTROL_NAMES:
        control = profile.controls.get(name)
        if isinstance(control, PerLayer):
            for layer, event in control.events:
                yield f"{name}.layers.{layer}", name, layer, event
        elif control is not None:
            yield name, name, None, control


def _cross_check(profile):
    """Problems that span controls or depend on the layer count (design 2.4, 2.9)."""
    problems = []
    first_initial = {}  # (channel, cc) -> (path, initial)
    for path, name, _layer, event in _each_action(profile):
        if isinstance(event, LayerSet) and _is_int(event.layer) and event.layer > profile.layer_count:
            problems.append(
                Problem(
                    name,
                    f"{path}.layer: layer {event.layer} doesn't exist (count = {profile.layer_count})",
                )
            )
        if isinstance(event, CcAbsolute) and event.initial is not None:
            channel = event.channel or profile.channel
            seen = first_initial.setdefault((channel, event.cc), (path, event.initial))
            if seen[1] != event.initial:
                problems.append(
                    Problem(
                        name,
                        f"{path}.initial: CC {event.cc} on channel {channel} starts at "
                        f"{event.initial}, but {seen[0]}.initial starts it at {seen[1]}; "
                        "use one start value",
                    )
                )
    return problems


# --- writing ------------------------------------------------------------------------------


def _event_data(event):
    """An event's TOML table: `kind` first, then fields that differ from their defaults."""
    table = {"kind": event.kind}
    for spec in _SPECS[event.kind]:
        value = getattr(event, spec.attr)
        if spec.default is _REQUIRED or value != spec.default:
            table[spec.key] = value
    return table


def _control_data(control):
    if isinstance(control, PerLayer):
        return {"layers": {str(n): _event_data(e) for n, e in control.events}}
    return _event_data(control)


def _profile_data(profile):
    """The profile as nested dicts in the fixed file order (design 2.8)."""
    layers = {"count": profile.layer_count}
    names = list(profile.layer_names)
    while names and not names[-1]:
        names.pop()
    if names:
        layers["names"] = names
    data = {
        "version": PROFILE_VERSION,
        "midi": {"port": profile.port, "channel": profile.channel},
        "pad": {"orientation": profile.orientation},
        "layers": layers,
    }
    if profile.lighting is not None:
        light = profile.lighting
        table = {"mode": light.mode, "brightness": light.brightness, "speed": light.speed}
        if light.color is not None:
            table["color"] = list(light.color)
        data["lighting"] = table
    keys, encs = {}, {}
    for name in CONTROL_NAMES:
        control = profile.controls.get(name)
        if control is None:
            continue
        part, _, rest = name.partition(".")
        if part == "key":
            keys[rest] = _control_data(control)
        else:
            number, _, which = rest.partition(".")
            encs.setdefault(number, {})[which] = _control_data(control)
    if keys:
        data["key"] = keys
    if encs:
        data["enc"] = encs
    return data


_ARRAY = re.compile(r"\[\n((?:    [^\n]*,\n)+)\]")
HEADER = (
    "# glra-osc profile (written by glra-osc). The format is documented in\n"
    "# glra_osc/default_profile.toml; control names are physical, whatever the orientation.\n"
)


def dumps_profile(profile):
    """The profile as TOML text. Raises ProfileError for a profile with problems."""
    problems = validate(profile)
    if problems:
        raise ProfileError(problems[0].message)
    text = tomli_w.dumps(_profile_data(profile))
    # tomli-w spreads arrays over lines; names and colour read better on one.
    text = _ARRAY.sub(
        lambda m: "[" + ", ".join(line.strip().rstrip(",") for line in m.group(1).splitlines()) + "]",
        text,
    )
    return HEADER + "\n" + text


def dump_profile(profile, path):
    """Write the profile to `path` atomically (temp file in the same directory, then rename),
    creating the directory if needed, so a reader never sees half a file."""
    path = Path(path)
    text = dumps_profile(profile)
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        mode = stat.S_IMODE(path.stat().st_mode)
    except OSError:
        umask = os.umask(0)
        os.umask(umask)
        mode = 0o666 & ~umask
    fd, tmp = tempfile.mkstemp(dir=path.parent, prefix=f".{path.name}.", suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            handle.write(text)
            handle.flush()
            os.fsync(handle.fileno())
        os.chmod(tmp, mode)
        os.replace(tmp, path)
    except BaseException:
        try:
            os.unlink(tmp)
        except OSError:
            pass
        raise


# --- edit helpers (design 4.6, 4.7) -------------------------------------------------------
# Each returns an `Edit`: the new profile and what the change threw away, so the app can ask
# first (call, look at `discarded`, keep or drop the result). A discard is reported only when
# something is lost: an event replaced by an equal one loses nothing.


@dataclass(frozen=True)
class Discarded:
    control: str
    layer: int | None  # None: the control's global event or layer key
    action: object


@dataclass(frozen=True)
class Edit:
    profile: Profile
    discarded: tuple[Discarded, ...] = ()


def _edit_error(name, message):
    return ProfileError(f"{name}: {message}")


def _check_control_name(profile, name):
    if name not in CONTROL_NAMES:
        raise _edit_error(name, "unknown control")


def _check_layer(profile, name, layer):
    if layer is not None and not (_is_int(layer) and 1 <= layer <= profile.layer_count):
        raise _edit_error(name, f"layer {layer!r} doesn't exist (count = {profile.layer_count})")


def _with_control(profile, name, control):
    controls = dict(profile.controls)
    if control is None:
        controls.pop(name, None)
    else:
        controls[name] = control
    return replace(profile, controls=_in_canonical_order(controls))


def _held(control):
    """[(layer or None, action)] for what a control holds."""
    if control is None:
        return []
    if isinstance(control, PerLayer):
        return list(control.events)
    return [(None, control)]


def _lost(name, items, keep=None):
    return tuple(Discarded(name, layer, act) for layer, act in items if act != keep)


def _check_event(name, event, layer=None):
    """Raise if `event` isn't acceptable on this control (kind and field ranges)."""
    path = name if layer is None else f"{name}.layers.{layer}"
    kinds = TURN_KINDS if name in TURN_CONTROLS else PRESS_KINDS
    kind = getattr(event, "kind", None)
    if kind in LAYER_KINDS:
        raise _edit_error(name, "use set_layer_key for a layer key")
    if kind not in kinds:
        raise _edit_error(name, f"kind {kind!r} doesn't belong on this control (expected one of {', '.join(kinds)})")
    if _parse_event(_event_data(event), path, kinds) != event:
        raise _edit_error(name, f"not a clean {kind} event: {event!r}")


def set_event(profile, name, layer, event):
    """Set the event of control `name` as shown on `layer` (1-based; None = the Global tab).

    * a global event is replaced, whichever layer is shown (it is the same on every layer);
    * a per-layer control gets `event` on `layer`;
    * an empty control gets it on `layer`, or globally when `layer` is None;
    * a layer key becomes an event the same way, losing the key (reported).
    A per-layer control can't be set from the Global tab: pick a layer.
    """
    _check_control_name(profile, name)
    _check_layer(profile, name, layer)
    _check_event(name, event, layer)
    control = profile.controls.get(name)
    shape = control_shape(control)
    if shape == "per-layer":
        if layer is None:
            raise _edit_error(name, "has different events on each layer; pick a layer to edit one")
        events = control.as_dict()
        events[layer] = event
        return Edit(_with_control(profile, name, PerLayer.of(events)))
    if shape == "global" or (shape == "none" and layer is None):
        return Edit(_with_control(profile, name, event))
    new = PerLayer.of({layer: event}) if layer is not None else event
    return Edit(_with_control(profile, name, new), _lost(name, _held(control)))


def clear_event(profile, name, layer=None):
    """Clear control `name`: one layer's event for a per-layer control when `layer` is given,
    otherwise (and for a global event or a layer key) the whole control."""
    _check_control_name(profile, name)
    _check_layer(profile, name, layer)
    control = profile.controls.get(name)
    if isinstance(control, PerLayer) and layer is not None:
        events = control.as_dict()
        gone = events.pop(layer, None)
        if gone is None:
            return Edit(profile)
        new = PerLayer.of(events) if events else None
        return Edit(_with_control(profile, name, new), (Discarded(name, layer, gone),))
    return Edit(_with_control(profile, name, None), _lost(name, _held(control)))


def make_global(profile, name, layer=None):
    """Per-layer to global (design 4.6): the event on `layer` (lowest layer when None) applies
    on every layer; the other layers' *different* events are discarded (reported). A control
    that is already global or a layer key stays as it is."""
    _check_control_name(profile, name)
    _check_layer(profile, name, layer)
    control = profile.controls.get(name)
    shape = control_shape(control)
    if shape == "none":
        raise _edit_error(name, "has no event to make global")
    if shape != "per-layer":
        return Edit(profile)
    events = control.as_dict()
    keep_layer = min(events) if layer is None else layer
    if keep_layer not in events:
        raise _edit_error(name, f"has no event on layer {keep_layer} to make global")
    keep = events[keep_layer]
    others = [(n, e) for n, e in control.events if n != keep_layer]
    return Edit(_with_control(profile, name, keep), _lost(name, others, keep=keep))


def make_per_layer(profile, name):
    """Global to per-layer (design 4.6): the global event is copied to every layer, so nothing
    changes in play. A per-layer control stays as it is."""
    _check_control_name(profile, name)
    control = profile.controls.get(name)
    shape = control_shape(control)
    if shape == "per-layer":
        return Edit(profile)
    if shape != "global":
        raise _edit_error(name, "has no global event to spread over the layers")
    copies = PerLayer.of({n: control for n in range(1, profile.layer_count + 1)})
    return Edit(_with_control(profile, name, copies))


def set_layer_key(profile, name, key):
    """Make press control `name` a layer key (`LayerSet`, `LayerInc` or `LayerDec`). Every
    event it held is discarded (reported); changing one layer key to another loses nothing."""
    _check_control_name(profile, name)
    if name in TURN_CONTROLS:
        raise _edit_error(name, "a dial turn can't be a layer key")
    if not isinstance(key, (LayerSet, LayerInc, LayerDec)):
        raise _edit_error(name, f"expected LayerSet, LayerInc or LayerDec, got {key!r}")
    if isinstance(key, LayerSet) and not (
        _is_int(key.layer) and 1 <= key.layer <= profile.layer_count
    ):
        raise _edit_error(
            f"{name}.layer", f"layer {key.layer!r} doesn't exist (count = {profile.layer_count})"
        )
    old = profile.controls.get(name)
    lost = () if control_shape(old) == "layer-key" else _lost(name, _held(old))
    return Edit(_with_control(profile, name, key), lost)


def add_layer(profile, name=""):
    """Append an empty layer (at most 8)."""
    if profile.layer_count >= MAX_LAYERS:
        raise ProfileError(f"layers.count: at most {MAX_LAYERS} layers")
    return Edit(
        replace(
            profile,
            layer_count=profile.layer_count + 1,
            layer_names=profile.layer_names + (name,),
        )
    )


def remove_layer(profile, layer):
    """Remove `layer`: its events are discarded (reported), the layers above it move down one.
    Per-layer controls left with no events disappear. Layer keys that point past the new count
    are left as they are for `validate` to flag, not silently changed (design 4.7). At least
    one layer always remains."""
    if profile.layer_count <= MIN_LAYERS:
        raise ProfileError("layers.count: at least one layer must remain")
    if layer is None:
        raise ProfileError("layers.count: no layer given to remove")
    _check_layer(profile, "layers", layer)
    controls, lost = {}, []
    for name, control in profile.controls.items():
        if not isinstance(control, PerLayer):
            controls[name] = control
            continue
        kept = {}
        for n, event in control.events:
            if n == layer:
                lost.append(Discarded(name, n, event))
            else:
                kept[n - 1 if n > layer else n] = event
        if kept:
            controls[name] = PerLayer.of(kept)
    names = profile.layer_names[: layer - 1] + profile.layer_names[layer:]
    new = replace(
        profile,
        layer_count=profile.layer_count - 1,
        layer_names=names,
        controls=_in_canonical_order(controls),
    )
    return Edit(new, tuple(lost))


def rename_layer(profile, layer, name):
    """Give `layer` a name (`""` unnamed)."""
    _check_layer(profile, "layers", layer)
    if layer is None:
        raise ProfileError("layers.names: no layer given")
    if not isinstance(name, str):
        raise ProfileError(f"layers.names: expected a string, got {name!r}")
    names = list(profile.layer_names)
    names[layer - 1] = name
    return Edit(replace(profile, layer_names=tuple(names)))
