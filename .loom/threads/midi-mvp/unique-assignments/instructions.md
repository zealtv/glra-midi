# unique-assignments — give all 25 actions distinct codes

**Writes to the device. Confirm with Bob before the first write.**
Suggested model: Sonnet, with the chosen layout in hand.

Firmware reports carry no physical control ID. As of 2026-11-12 the three
encoders share identical consumer codes, so they can't be told apart.
Pick 25 distinct assignments that suit the route chosen in `suppression-route`,
then:
- The stock table as read on 2026-11-12 sits beside this file
  (`stock-backup-2026-11-12.json`, glra-studio `macropad backup` format).
- Back up the full assignment table again first (vendored `transactions`/`storage`
  do this; keep the backup in-repo under `device/backups/`, since it lets us restore
  the stock numpad layout).
- Write slot by slot with the vendored `write_one` (backup + readback
  verification). Slot map from glra-studio's protocol notes: keys rows
  `[0,1,2,3] [7,8,9,10] [14,15,16,17] [21,22,23,24]`; encoder groups
  (push, CW, CCW) `(4,5,6) (11,12,13) (18,19,20)`. Profile 0 only.
- Commit the layout as data (`device/layout.json`: slot → physical control
  → expected usage). The decoder reads this file, so the mapping lives in exactly one place.
- Add a `glra-osc device restore <backup>` path (or document the
  glra-studio route) so Bob can put the stock layout back.
- Have Bob press each control once to confirm the layout.
