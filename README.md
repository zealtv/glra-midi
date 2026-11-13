# glra-osc

Host-side middleware that turns the G-LRA K16_N3 macropad into a silent MIDI
controller (OSC later). It builds on [glra-studio](https://github.com/imolitor/glra-studio)
for device I/O.

**Status:** pre-alpha, but working. As of 2026-11-12 `glra-osc run` sends the pad's
16 keys and 3 encoders as MIDI on a virtual port and silences the pad so it doesn't
type into apps; Bob checked it with a DAW the same day. OSC output doesn't exist yet.
Planned work lives on the loom (`.loom/`); as of 2026-11-12 the MIDI MVP is done.

## Usage

macOS only. Install into a virtualenv (see "Setup and tests" below; call `.venv/bin/glra-osc` or activate it), then:

```sh
glra-osc run                  # virtual MIDI port "GLRA K16", channel 1, shipped mapping
glra-osc run --dry-run        # print the MIDI messages instead of sending them
glra-osc run --config my.toml # use your own mapping file
glra-osc monitor              # read-only live view of decoded control events
glra-osc monitor --raw        # ...plus each raw report as hex
glra-osc monitor --profile p.toml  # number events as displayed in the profile's [pad] orientation
glra-osc unsilence            # remove glra-osc's key-mapping entries from the pad
```

- **Mapping.** Without `--config`, `run` uses `glra_osc/default_mapping.toml`: keys 1-16 send
  notes 36-51, the three encoders send relative CCs 16-18, and their pushes send notes 52-54.
  Copy that file, edit it and pass it with `--config`; it documents every field, and a
  typo in a key name is an error naming the key.
- **Orientation.** A profile's `[pad] orientation` (`dials-top`, `dials-right`, `dials-bottom`,
  `dials-left`) sets how controls are numbered and drawn; the file itself keeps physical names
  (`key.13`), so turning the pad remaps nothing. `monitor --profile` prints `KEY 01 [key.13] DOWN`
  (displayed number, physical id in brackets). Clockwise stays clockwise. The firmware's lighting
  animations run in the vendor's frame (dials on the right) whatever orientation you choose.
  Directions get confirmed at the pad on the config-app tour (design: `docs/config-app.md` §6).
- **Silencing.** While `run` or `monitor` runs, it maps the pad's codes to "no event" with
  `hidutil`, so the pad stays quiet for the system and only glra-osc hears it. Your own
  entries on the pad (for example a CapsLock remap) stay. On exit (Ctrl-C or SIGTERM) it
  removes only its own entries. After `kill -9` the entries stay until you replug the pad
  or run `glra-osc unsilence`. If the pad can't be silenced, `run` and `monitor` refuse to
  start; `--allow-typing` starts them anyway, and the pad then types into the focused app.
- **Known gap: the first ~3 s after a (re)plug.** For about 3 s after the pad connects, macOS
  puts its own key mapping back whenever glra-osc sets one (observed 2026-11-12, macOS 14.6).
  glra-osc re-checks every 100 ms and repairs it, but a key pressed in one of those short gaps
  can still type into the focused app. Wait a few seconds after plugging the pad in before
  playing.
- Stop with Ctrl-C.

## Setup and tests

Needs Python 3.13+ on macOS (Homebrew's `python3.14` works).

```sh
/opt/homebrew/bin/python3.14 -m venv .venv
.venv/bin/pip install -e '.[dev,gui]'   # gui: PySide6, for the configuration app
./test.sh          # ruff + unittest (the app tests skip without the gui extra)
.venv/bin/glra-osc --version
```

The configuration app (work in progress: it shows a profile's layers and tiles and opens,
saves and reloads profiles; editing fields come later) starts with `glra-osc config`
or `glra-osc-config`; `glra-osc config --demo` runs it on a throwaway fixture profile.
`tools/app-capture.sh <state> <out.png>` renders a named state offscreen.

## Licence

GPL-3.0-only, because it reuses glra-studio code. See `LICENSE` and
`THIRD_PARTY_NOTICES.md`.
