# Changelog

All notable changes to glra-midi go in this file. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and the project follows
[Semantic Versioning](https://semver.org/) with the 0.x rule in `docs/releasing.md`: during
0.x a minor bump (0.1 to 0.2) may break the profile format or the command line.

Each release gets a `## [X.Y.Z] - YYYY-MM-DD` section; `tools/release-check.sh` fails when the
version in `glra_midi/__init__.py` has none. The 0.1.0 section was drafted on 2026-11-13 from
the loom's tied stitches (`midi-mvp`, `config-app`) and the README, and Bob read it before the
release.

## [Unreleased]

### Changed

- Profile files are stricter about two spellings that used to load. A control or layer table
  written with extra zeros or a sign (`[key."01"]`, `layers."01"`) now fails with "unknown control"
  or "layer doesn't exist", where before it loaded as key 1 and silently beat a `[key.1]` table
  written earlier in the file. `version = 1.0` (a float) now fails with "this glra-midi reads
  version 1"; write `version = 1`. Files the app saves, and the shipped default profile, use
  neither spelling.

### Fixed

- Config app: the Inspector's "Layers 1 and 3 hold an event…" note now says "holds" for a
  single layer. The words behind the Channel and Layer pickers, the lighting hint and the "Pad now"
  line moved from QML into the Python model, with no change to what they show.
- Config app: [Select] on a Problems row now also switches to the layer the problem names
  (for a problem at `key.4.layers.3`, layer 3), so the inspector shows the control the message
  talks about. A problem that names no layer leaves the tab alone.
- Config app: a profile changed on disk while a confirmation or "Save changes?" dialog is open
  no longer reloads underneath it, so answering OK can't apply an edit built on the old profile
  and drop the reload. The change is noticed right after the dialog closes.
- Config app: a MIDI port the field refuses (an empty name) now counts as an unsaved change:
  the title shows the `•`, quitting and Open ask first, and Save says "Fix the MIDI port before
  saving" instead of writing the old port under a field that showed something else.
- Config app: removing a layer now renumbers the `layer-set` keys that point above it, so
  each keeps reaching the same layer, and flags a key that pointed at the removed layer in the
  Problems list (it shows as `→ L?` until you pick another layer). Before, such keys kept their
  number and silently went to a different layer.
- Applying a lighting mode no longer reports "Written to the pad, but it did not
  read back as expected" when the pad only normalised bytes it ignores (firmware
  103 resets the colour to `ff ff ff` with One colour off, and rewrites an unused
  byte with it on). Any other difference still shows. The app's "Pad now" line
  shows what the pad holds.

## [0.1.0] - 2026-11-13

First public release. The project began as `glra-osc` and was renamed
`glra-midi` on 2026-11-13.

### Added

- `glra-midi run`: plays a profile on a virtual CoreMIDI port named "GLRA K16" (via `rtmidi2`).
  All 25 physical controls (16 keys; 3 dials, each turn left, turn right and push) work.
  Keys and dial pushes send notes (momentary or latch) or CCs; dial turns send relative or
  absolute CCs.
- Profiles: a TOML file (`version = 1`) with 1 to 8 layers, per-layer or global events, layer
  keys (`layer-set`, `layer-inc`, `layer-dec`), a channel that follows the layer, CC glides
  (rise, fall and ease times, easing curves) and a `[pad] orientation`. The shipped default
  (`glra_midi/default_profile.toml`) documents every field.
- Hot reload: `run` notices a saved or switched profile within half a second and reloads it.
- Silencing: while `run` or `monitor` runs, the pad's keystrokes are mapped to "no event" with
  `hidutil`, without root; `glra-midi unsilence` clears the entries after a crash.
- `glra-midi config`: a configuration app (PySide6, the `gui` extra) with layer tabs, the pad
  drawn in its orientation, an inspector for each control, profile save, save as and open,
  and a device panel; `--demo` runs it on a fake pad and a throwaway profile folder.
- Factory RGB lighting modes, from the app's device panel or `glra-midi lights --apply`.
  Each write is saved in the pad's flash, so both ask first and read the result back.
- `glra-midi monitor`: a read-only live view of decoded control events, with `--raw` and
  `--profile` for the profile's orientation.
- `glra-midi run --dry-run`: prints events, layer changes and MIDI instead of sending them.
- `LICENSE` (GPL-3.0-only) and `THIRD_PARTY_NOTICES.md` for the code taken from glra-studio.

### Changed

- The profile folder moved from `~/Library/Application Support/glra-osc/` to
  `~/Library/Application Support/glra-midi/`. The first `glra-midi` command or app start
  moves an old folder across and says so once.

### Known limits

- macOS only; no OSC output yet; no MIDI input or LED feedback.
- For about 3 s after the pad is plugged in, a key press can still type into the focused app
  (README, "Known gap").
