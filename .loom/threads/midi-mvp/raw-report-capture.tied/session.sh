#!/bin/zsh
# Guided hardware session, 2026-11-12. Restores mapping + volume on exit.
cd "${0:A:h}"
PY=/Users/bob/repos/glra-studio/.venv/bin/python
M='{"VendorID":0x36ae,"ProductID":0x2475}'
# Bob's existing per-device mapping (CapsLock -> Left Cmd), observed 2026-11-12.
ORIG='{"UserKeyMapping":[{"HIDKeyboardModifierMappingSrc":0x700000039,"HIDKeyboardModifierMappingDst":0x7000000E3}]}'
VOL=$(osascript -e 'output volume of (get volume settings)'); MUTED=$(osascript -e 'output muted of (get volume settings)')
restore() {
  hidutil property --matching "$M" --set "$ORIG" >/dev/null
  osascript -e "set volume output volume $VOL" -e "set volume output muted $MUTED"
  echo "restored pad mapping and volume ($VOL, muted $MUTED)"
}
trap restore EXIT INT TERM
hidutil property --matching "$M" --get UserKeyMapping > captures/mapping-before.txt
echo "K16 hardware session: keep THIS pane focused (pad keystrokes are caught here). About 4-5 minutes."; for i in 8 7 6 5 4 3 2 1; do printf "\rstarting in %s " $i; sleep 1; done; echo
$PY capture.py capture captures/1-capture.jsonl
# Test map: each key row -> a different candidate "no-op" destination; dials -> three more.
m() { printf '{"HIDKeyboardModifierMappingSrc":%s,"HIDKeyboardModifierMappingDst":%s},' $1 $2 }
TEST="{\"UserKeyMapping\":[$(m 0x700000039 0x7000000E3)\
$(m 0x70000005F 0x700000000)$(m 0x700000060 0x700000000)$(m 0x700000061 0x700000000)$(m 0x700000056 0x700000000)\
$(m 0x70000005C 0x7000000FF)$(m 0x70000005D 0x7000000FF)$(m 0x70000005E 0x7000000FF)$(m 0x700000057 0x7000000FF)\
$(m 0x700000059 0x70000007E)$(m 0x70000005A 0x70000007E)$(m 0x70000005B 0x70000007E)$(m 0x700000054 0x70000007E)\
$(m 0x700000055 0x7000000A5)$(m 0x700000062 0x7000000A5)$(m 0x700000063 0x7000000A5)$(m 0x700000058 0x7000000A5)\
$(m 0xC000000E2 0xC00000000)$(m 0xC000000E9 0x700000000)$(m 0xC000000EA 0x7000000FF)]}"
TEST=${TEST/,]/]}
echo "$TEST" > captures/test-mapping.json
hidutil property --matching "$M" --set "$TEST" > captures/mapping-set-output.txt 2>&1
hidutil property --matching "$M" --get UserKeyMapping > captures/mapping-during.txt
osascript -e "set volume output volume $VOL" -e "set volume output muted $MUTED"
$PY capture.py suppress captures/2-suppress.jsonl
$PY capture.py replug captures/3-replug.jsonl
echo; echo "ALL DONE — thanks Bob. You can walk away; Claude will take it from here."
