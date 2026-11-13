
Fixes from Bob's tour of the configuration app, after 0.1.0.

### Changed

- Profile files are stricter about two spellings that used to load. A control or layer table
  written with extra zeros or a sign (`[key."01"]`, `layers."01"`) now fails with "unknown control"
  or "layer doesn't exist", where before it loaded as key 1 and silently beat a `[key.1]` table
  written earlier in the file. `version = 1.0` (a float) now fails with "this glra-midi reads
  version 1"; write `version = 1`. Files the app saves, and the shipped default profile, use
  neither spelling.

### Fixed

- Config app: the first line of a key tile now shrinks to fit instead of ending in "…", so
  `CC20 10↔120` shows whole. (The second line, such as `↑250 ↓600 ms ease-out`, still cuts off
  on a narrow tile; the tooltip has it in full.)
- Config app: with the device panel open the pad view no longer shrinks to about two thirds of
  its size at the default window size. The window starts 820 px high (was 740) and the panel is a
  little more compact ("Pad now" shares the lighting heading's line).
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
- Config app: quitting no longer ends with a "Python quit unexpectedly" crash report on macOS.
  hidapi was first loaded on the pad worker thread, and at exit its shutdown hook closed the
  device manager against that thread's already-gone run loop. The app now loads it on the main
  thread when it starts.
- Config app: removing a layer now renumbers the `layer-set` keys that point above it, so
  each keeps reaching the same layer, and flags a key that pointed at the removed layer in the
  Problems list (it shows as `→ L?` until you pick another layer). Before, such keys kept their
  number and silently went to a different layer.
- Applying a lighting mode no longer reports "Written to the pad, but it did not
  read back as expected" when the pad only normalised bytes it ignores (firmware
  103 resets the colour to `ff ff ff` with One colour off, and rewrites an unused
  byte with it on). Any other difference still shows. The app's "Pad now" line
  shows what the pad holds.

