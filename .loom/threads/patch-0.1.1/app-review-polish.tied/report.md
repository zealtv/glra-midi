# app-review-polish: report

Worker: Claude Sonnet 5.5, 2026-11-13 (paused once for usage, then resumed). Seven review
findings and the pad-view shrinking, one commit each, cheapest first. `./test.sh` passed
(621 tests) after merging main (`76135a3`).

## What I built

| Item | Commit | Change |
| --- | --- | --- |
| 13 | `0afb051` | `lighting.data_dir` calls `profile.app_dir`; a test says they agree. |
| 11 | `d16f783` | A table name must be the plain number: `[key."01"]`, `layers."01"`, `"+1"` now fail ("unknown control" / "layer doesn't exist"), as does `version = 1.0`. CHANGELOG "Changed" says so. |
| 10 | `8ca0b86` | An invalid port draft counts as unsaved (title `•`, quit and Open ask) and blocks Save and Save As with "Fix the MIDI port before saving: …". |
| 9 | `f9eac61` | `Controller.poll` does nothing while a confirm or unsaved prompt is pending; the stale stamps mean the change is noticed on the first poll after the answer. |
| 8 | `141e255` | Each problem row carries a `layer`; new slot `selectProblem(index)` sets tab and control; the [Select] button calls it. A problem whose path names no layer leaves the tab alone. |
| 12 | `ef8c5e1` | The channel and layer picker choices, the lighting hint, the "Pad now" line and the "Layers … hold an event" note come from Python (`inspector.describe`, `describe_lighting`, `_device_model`). Side effect: "holds" for a single layer (it said "Layer 2 hold"). |
| 5 | `58c13a3` | Tile line 1 uses `fontSizeMode: HorizontalFit` (minimum 9 px), so `CC20 10↔120` shows whole. |
| pad view | `a26e6d1` | See below. |

**Pad view.** The pad is drawn with a `scale` that shrinks when its area is short. With the device
panel open at 1000 × 740 the scale was 0.66 (measured with a probe: area 303 px, pad needs 432).
Now: default window 820 px high (was 740), panel margins and spacing tightened, "Pad now" shares
the line with the lighting heading, pad row spacing 14 → 10. Scale is now 0.93 in all four
orientations (the sideways ones were already fine). A test (`DevicePanelTests`) fails below 0.9.
`docs/config-app.md` 4.3 now says 1000 × 820. macOS clamps a window to the screen, so on a short
display the pad shrinks a little again; I did not test a real small screen.

## How I checked

- `./test.sh` before every commit; each fix has a test that failed first or exercises the new path
  (controller tests for 8, 9, 10; profile tests for 11; model tests for 12; a QML test for the pad).
- Item 11: loaded the shipped default, `demo_profile.toml` and every `tests/fixtures/*.toml`
  directly; all still load.
- Captures in `captures/` (offscreen, `--demo`, fake pad), looked at: `after-12-*.png` (text
  unchanged after the move to Python), `after-5-cc-momentary.png`, `after-pad-device-panel.png`
  and `-dark.png`. I read the light ones; I did not read the dark device-panel capture closely.
- Nothing wrote to the pad; no run against a real pad.

## What I didn't do

- Tile line 2 (`↑250 ↓600 ms ease-out`) still elides on a narrow tile. Fitting it needed 8 px
  text, which read worse than the cut-off, so I left it (the tooltip has the full text). CHANGELOG
  says so.
- Strings still composed in QML after 12: the tile accessible names and tooltip, "Layer " in the
  tab accessible name, and "Rename layer " in the rename dialog heading. The review named only the
  Inspector and DevicePanel ones.
- Item 10 blocks Save rather than saving the old port; item 9 only guards the poll (not Revert
  or Open reading the disk while a prompt is open).

## Open questions

None for Bob. Two small calls I made that he may want to see: the 820 px default height, and
blocking Save on an invalid port draft.
