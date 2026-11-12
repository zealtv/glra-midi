# SPDX-License-Identifier: GPL-3.0-only

"""The mapping file: which MIDI message each logical control sends.

A mapping is a small TOML file (see `default_mapping.toml`, which documents the
format). `load_mapping` / `parse_mapping` validate it into the frozen
dataclasses below and raise `MappingError`, with the offending key path in the
message (for example ``enc.2.turn.step``), on anything unexpected. Unknown keys
are errors so that typos do not silently do nothing.

This module only describes the mapping. Sending MIDI, toggle state and absolute
encoder values belong to `midi-out`.
"""

import tomllib
from dataclasses import dataclass, field
from importlib import resources
from pathlib import Path

KEY_COUNT = 16
ENCODER_COUNT = 3
BUTTON_MODES = ("momentary", "toggle")
RELATIVE_ENCODINGS = ("twos-complement", "binary-offset", "signed-bit")
DEFAULT_PORT = "GLRA K16"
DEFAULT_CHANNEL = 1


class MappingError(ValueError):
    """The mapping file is unreadable or invalid; the message names the key."""


@dataclass(frozen=True)
class NoteBinding:
    note: int
    velocity: int = 127
    mode: str = "momentary"


@dataclass(frozen=True)
class CcBinding:
    cc: int
    on: int = 127
    off: int = 0
    mode: str = "momentary"


@dataclass(frozen=True)
class RelativeTurn:
    cc: int
    encoding: str = "twos-complement"


@dataclass(frozen=True)
class AbsoluteTurn:
    cc: int
    initial: int = 64
    step: int = 1


Binding = NoteBinding | CcBinding
Turn = RelativeTurn | AbsoluteTurn


@dataclass(frozen=True)
class Mapping:
    port: str = DEFAULT_PORT
    channel: int = DEFAULT_CHANNEL  # 1..16, as written in the file
    keys: dict[int, Binding] = field(default_factory=dict)  # key 1..16 -> binding
    enc_push: dict[int, Binding] = field(default_factory=dict)  # encoder 1..3 -> binding
    enc_turn: dict[int, Turn] = field(default_factory=dict)  # encoder 1..3 -> turn

    @property
    def midi_channel(self):
        """The channel as the 0..15 value that goes into a MIDI status byte."""
        return self.channel - 1


def default_mapping_path():
    return Path(str(resources.files("glra_osc").joinpath("default_mapping.toml")))


def load_mapping(path=None):
    """Load and validate a mapping file; with no path, the shipped default."""
    path = default_mapping_path() if path is None else Path(path)
    try:
        text = path.read_text(encoding="utf-8")
    except OSError as err:
        raise MappingError(f"{path}: cannot read mapping file: {err.strerror or err}") from err
    return parse_mapping(text, source=str(path))


def parse_mapping(text, source="<mapping>"):
    try:
        data = tomllib.loads(text)
    except tomllib.TOMLDecodeError as err:
        raise MappingError(f"{source}: not valid TOML: {err}") from err
    try:
        return _build(data)
    except MappingError as err:
        raise MappingError(f"{source}: {err}") from None


# --- validation helpers; every message starts with the key path ---------------------------


def _table(value, path):
    if not isinstance(value, dict):
        raise MappingError(f"{path}: expected a table, got {value!r}")
    return value


def _check_keys(table, allowed, path):
    for name in table:
        if name not in allowed:
            where = f"{path}.{name}" if path else name
            raise MappingError(f"{where}: unknown key (allowed here: {', '.join(allowed)})")


def _int(table, name, path, lo, hi, default=None):
    where = f"{path}.{name}"
    if name not in table:
        if default is None:
            raise MappingError(f"{where}: required")
        return default
    value = table[name]
    if isinstance(value, bool) or not isinstance(value, int) or not lo <= value <= hi:
        raise MappingError(f"{where}: expected an integer {lo}..{hi}, got {value!r}")
    return value


def _choice(table, name, path, choices, default):
    value = table.get(name, default)
    if value not in choices:
        raise MappingError(f"{path}.{name}: expected one of {', '.join(choices)}, got {value!r}")
    return value


def _binding(table, path):
    table = _table(table, path)
    if ("note" in table) == ("cc" in table):
        raise MappingError(f"{path}: needs exactly one of 'note' or 'cc'")
    if "note" in table:
        _check_keys(table, ("note", "velocity", "mode"), path)
        return NoteBinding(
            note=_int(table, "note", path, 0, 127),
            velocity=_int(table, "velocity", path, 1, 127, default=127),
            mode=_choice(table, "mode", path, BUTTON_MODES, "momentary"),
        )
    _check_keys(table, ("cc", "on", "off", "mode"), path)
    return CcBinding(
        cc=_int(table, "cc", path, 0, 127),
        on=_int(table, "on", path, 0, 127, default=127),
        off=_int(table, "off", path, 0, 127, default=0),
        mode=_choice(table, "mode", path, BUTTON_MODES, "momentary"),
    )


def _turn(table, path):
    table = _table(table, path)
    kind = table.get("type")
    if kind == "relative":
        _check_keys(table, ("type", "cc", "encoding"), path)
        return RelativeTurn(
            cc=_int(table, "cc", path, 0, 127),
            encoding=_choice(table, "encoding", path, RELATIVE_ENCODINGS, "twos-complement"),
        )
    if kind == "absolute":
        _check_keys(table, ("type", "cc", "initial", "step"), path)
        return AbsoluteTurn(
            cc=_int(table, "cc", path, 0, 127),
            initial=_int(table, "initial", path, 0, 127, default=64),
            step=_int(table, "step", path, 1, 127, default=1),
        )
    raise MappingError(f"{path}.type: expected 'relative' or 'absolute', got {kind!r}")


def _numbered(table, count, path):
    """Yield (number, subtable) for a table keyed "1".."count"."""
    table = _table(table, path)
    for name, sub in table.items():
        if not (name.isascii() and name.isdigit() and 1 <= int(name) <= count):
            raise MappingError(f"{path}.{name}: unknown control (expected 1..{count})")
        yield int(name), sub


def _build(data):
    _check_keys(data, ("global", "key", "enc"), "")

    glob = _table(data.get("global", {}), "global")
    _check_keys(glob, ("port", "channel"), "global")
    port = glob.get("port", DEFAULT_PORT)
    if not isinstance(port, str) or not port.strip():
        raise MappingError(f"global.port: expected a non-empty string, got {port!r}")
    channel = _int(glob, "channel", "global", 1, 16, default=DEFAULT_CHANNEL)

    keys = {
        n: _binding(sub, f"key.{n}") for n, sub in _numbered(data.get("key", {}), KEY_COUNT, "key")
    }

    enc_push, enc_turn = {}, {}
    for n, sub in _numbered(data.get("enc", {}), ENCODER_COUNT, "enc"):
        path = f"enc.{n}"
        sub = _table(sub, path)
        _check_keys(sub, ("push", "turn"), path)
        if "push" in sub:
            enc_push[n] = _binding(sub["push"], f"{path}.push")
        if "turn" in sub:
            enc_turn[n] = _turn(sub["turn"], f"{path}.turn")

    return Mapping(port=port, channel=channel, keys=keys, enc_push=enc_push, enc_turn=enc_turn)
