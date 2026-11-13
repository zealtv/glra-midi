# profile-model: report

Claude (Sonnet worker), 2026-11-13, branch `profile-model`. Pure code and
tests; no device I/O, no pad writes. `./test.sh` passed (241 tests) before the
commit and after merging `main` (already up to date: nothing to merge).

## What I built

- `glra_osc/profile.py` (1015 lines), built to `docs/config-app.md` §2 and
  §4.6–4.7.
  - **Model.** Frozen dataclasses per kind: `Note`, `CcMomentary`, `CcSet`,
    `CcStep`, `LayerSet`, `LayerInc`, `LayerDec`, `CcRelative`, `CcAbsolute`;
    `PerLayer`; `Lighting`; `Profile`. A control holds one thing: an event or
    layer key (global), or a `PerLayer`. The types make "global, per-layer and
    layer key exclude each other" hold in code; the parser rejects mixed files
    with a message naming the control (`key.13: a layer key can't also have
    per-layer events`, `key.4.layers.1: layer keys are global; move it to
    [key.4]`).
  - **Parsing.** `parse_profile` / `load_profile`; errors start with the key
    path, unknown keys are errors. One table of field specs (`_SPECS`) drives
    parsing, writing and edit-time checking. Cross-control checks: `layer-set`
    above the count (`enc.2.push.layer: layer 6 doesn't exist (count = 4)`)
    and conflicting `initial`s for one (channel, cc), naming both controls.
  - **`validate(profile)`** returns every problem as `Problem(control,
    message)`, with the same words as parsing. The edit helpers can leave a
    profile with problems (a layer key past the last layer after a removal),
    so the app needs this; its `control` field serves the "[Select]" button.
  - **Writing.** `dump_profile` (atomic: temp file in the same directory,
    `fsync`, `os.replace`; creates the directory; keeps an existing file's mode)
    and `dumps_profile`, both refusing a profile with problems. Fixed order per
    §2.8; event fields equal to their defaults are left out; `tomli-w`'s
    multi-line arrays are collapsed to one line (`names`, `color`). Round trip
    tested over a profile using every kind, the §2.5 example, the default
    profile and awkward strings.
  - **Paths.** `default_profile_path()`, `user_profile_path(home=None)`; the
    directory name comes from one constant, `APP_DIR_NAME` (Q9).
  - **Legacy.** A file without `version` goes through `mapping.parse_mapping`
    and `profile_from_mapping` (one layer, all global; `toggle` becomes
    `latch`, `on`/`off` become `high`/`low`, the old default start of 64 stays
    explicit on absolute dials). `is_legacy_mapping(text)` lets the app say
    "Opened an old mapping file…". `mapping.py` and `Engine` are untouched.
  - **Edit helpers** (§4.6, 4.7): `set_event`, `clear_event`, `make_global`,
    `make_per_layer`, `set_layer_key`, `add_layer`, `remove_layer`,
    `rename_layer`. Each returns an `Edit(profile, discarded)`; `discarded`
    lists what the change throws away (events replaced by an equal one count
    as nothing lost), so the app calls the helper, asks if `discarded` isn't
    empty, and keeps or drops the result.
- `glra_osc/default_profile.toml`, generated then given a header documenting
  the format. Content per §2.7: 4 layers, per-layer notes 36–99, dial pushes
  previous / layer 1 / next, global relative CC 16–18, no `[lighting]`. Ships
  as package data through the existing `*.toml` glob.
- `pyproject.toml`: `tomli-w==1.2.0` (installed into `.venv`).
- `tests/test_profile.py`: 88 tests. Covers every kind, the §2.5 example, each
  validation error's path, round trip, atomic write, legacy files (the default
  mapping and a toggled CC), the default profile, every edit helper including
  layer removal and renumbering.

## What I didn't build

- **No `Profile` to `Mapping` adapter.** The stitch called it optional;
  nothing needs it yet (`runner-profile` wires `run`, and `layer-engine`
  replaces `Engine`'s input).
- **No comment detection** for the app's "this file had comments" warning
  (§2.8); `tomllib` drops comments, so the app stitch needs its own scan.
- **No profile-to-engine glue**, no CLI changes, no docs/README changes.
- **No `THIRD_PARTY_NOTICES.md` entry** for `tomli-w` (MIT): that file lists
  vendored code, and tomli-w is an installed dependency. Say if you want it
  listed.

## Choices worth a look

- **Top-level sections are always written** (`[midi]`, `[pad]`, `[layers]`,
  all of `[lighting]`'s fields), even at their defaults. I read §2.8's "leaves
  out fields equal to their defaults" as applying to event fields; the sections
  describe the pad and read better in a hand-edited file. Event fields at
  their defaults are left out; `channel` is written whenever set, even when it
  equals the default, so the file keeps what the user chose.
- **Control names.** The profile names a dial turn `enc.N.turn`; `events.py`
  emits `enc.N` for turns (and `enc.N.push`). `layer-engine` needs that
  mapping.
- **Set from the Global tab.** `set_event` on a per-layer control with no
  layer given raises `ProfileError`: the design hides those fields on the
  Global tab, so the app shouldn't call it.

## How I checked

`./test.sh` (ruff plus 241 tests, 88 new) passes. I also loaded the shipped
default and round-tripped it by hand. Nothing touched the device: the module
has no device imports.

## Open questions

`questions.md` here: P1 (what `remove_layer` does to `layer-set` keys) and P2
(lighting defaults). Both took the design's rule or an obvious default.
