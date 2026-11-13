# References: how other configurators lay out "pick a control, edit it, switch layer"

Desk research by Claude (Opus worker on `config-design`), 2026-11-13, from one
web search per tool and Claude's prior knowledge of these apps. Links only; no
screenshots, looks or assets copied. Treat the notes as "as these pages read on
2026-11-13"; vendors revise their apps often.

## Novation Components (Launch Control XL, Launchkey, Launchpad custom modes)

- https://userguides.novationmusic.com/hc/en-gb/articles/26190535820562-Using-Custom-Modes-on-the-Launch-Control-XL-3
- https://support.novationmusic.com/hc/de/articles/207561145-Edit-Launch-Control-XL-MK1-MK2-MIDI-messages
- https://components.novationmusic.com

Notes: a picture of the hardware fills the page; click a control and a side
panel edits it (message type, channel, number, min/max, LED colour). Each
control on the picture carries a short label of what it sends. A "custom mode"
works like a whole-device page, picked from a list; editing happens off-device
and reaches the hardware only on an explicit "Send to …". The device holds the
mode, so Components treats a file and the device as two separate places.

**Borrow:** the pad picture as the main surface, a tile label per control, a
side inspector, and the explicit send step (ours: lighting **Apply** only).

## Akai MPK mini Editor

- https://cdn.inmusicbrands.com/akai/mpk-mini-mk2/MPK_mini_MKII_Editor_-_User_Guide_-_v1.0.pdf
- https://support.akaipro.com/en/support/solutions/articles/69000798941-akai-pro-mpk-mini-play-how-to-use-the-editor

Notes: "programs" (whole-device presets) chosen from a drop-down; the window
draws the pads and knobs in place with editable fields inside each one; pads
come in banks A/B shown one at a time. Get from / send to the device as
separate buttons.

**Borrow:** a bank/layer switch that redraws the whole surface at once (Bob:
"layers can be edited and viewed as a whole"). **Avoid:** fields crammed into
each tile; on 16 small tiles that gets hard to read, so we keep a summary on
the tile and the fields in the inspector.

## Arturia MIDI Control Center

- https://www.arturia.com/technology/mcc
- https://manualmachine.com/arturia/midicontrolcenter/18990845-users-manual

Notes: device picture centre, a list of saved templates ("User Maps") on one
side, a parameter panel for the clicked control (mode, channel, CC, min, max,
behaviour: momentary/toggle). A SYNC toggle, when lit, pushes each edit to the
device's working memory at once.

**Borrow:** the per-control "behaviour" picker (our action kind), min/max as
plain number fields. **Avoid:** live sync: our pad persists every lighting
write to flash (`glean:k16n3-lighting`), so nothing writes on edit.

## Intech Grid Editor

- https://grid-documentation.onrender.com/guides/grid/grid-basic/editor-121-button
- https://grid-documentation.onrender.com/guides/grid/grid-basic/editor-121-encoder
- https://grid-documentation.onrender.com/wiki/events/ui-events/button-event

Notes (a docs mirror; not checked against Intech's own site): select a control
on the module picture; the editor shows its events (setup, button, encoder) as
stacked action blocks. Four "pages" per module work like layers, picked by tabs
above the picture; a page's "setup" event sets defaults when it becomes active.
Buttons run momentary by default, toggle optional; encoders relative or
absolute.

**Borrow:** page tabs above the picture; momentary/toggle as a field of the
event, not a separate kind; relative vs absolute dial modes. **Avoid:** the
general action-block scripting; Bob's brief names a fixed set of kinds.

## Elgato Stream Deck

- https://marketplace.elgato.com/learn/inspiration/Profiles-Pages-Folders
- https://docs.elgato.com/stream-deck/profiles/getting-started

Notes: a key grid in the middle, an action list to drag onto keys, the
selected key's settings in a panel below. Profiles (whole setups) come from a
drop-down; pages (up to ten per profile) work like tabs, and "Next/Previous
Page" actions on keys switch them on the device. On Stream Deck+ the page
navigation keys appear on every page.

**Borrow:** page-navigation keys that sit on every page; this matches Bob's
"any press set to change layer becomes global". Show them as locked on each
layer tab. **Avoid:** drag-and-drop from an action palette; a kind picker in
the inspector serves 16 keys and 3 dials well enough.

## What the design takes from all five

1. The pad drawn in the middle as the main surface; click to select.
2. Short summary text on each tile; full fields in one inspector panel.
3. Layer tabs over the picture that redraw the whole layer.
4. Layer-switch controls shown on every layer, marked as such.
5. Device writes only on an explicit button, never live.
