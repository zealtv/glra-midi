#!/bin/zsh
# Consumer-usage UserKeyMapping test (non-root), 2026-11-12. Restores on exit.
cd "${0:A:h}"
M='{"VendorID":0x36ae,"ProductID":0x2475}'
O='{"HIDKeyboardModifierMappingSrc":0x700000039,"HIDKeyboardModifierMappingDst":0x7000000E3}'
VOL=$(osascript -e 'output volume of (get volume settings)'); MUTED=$(osascript -e 'output muted of (get volume settings)')
trap 'hidutil property --matching "$M" --set "{\"UserKeyMapping\":[$O]}" >/dev/null; osascript -e "set volume output volume $VOL" -e "set volume output muted $MUTED"; echo restored' EXIT INT TERM
# CW (vol-, E A) -> 0xC00000000 ; CCW (vol+, E9) -> 0x700000000 ; push (mute, E2) -> 0x7000000FF
hidutil property --matching "$M" --set "{\"UserKeyMapping\":[$O,{\"HIDKeyboardModifierMappingSrc\":0xC000000EA,\"HIDKeyboardModifierMappingDst\":0xC00000000},{\"HIDKeyboardModifierMappingSrc\":0xC000000E9,\"HIDKeyboardModifierMappingDst\":0x700000000},{\"HIDKeyboardModifierMappingSrc\":0xC000000E2,\"HIDKeyboardModifierMappingDst\":0x7000000FF}]}" > captures/dials-set-output.txt 2>&1
hidutil property --matching "$M" --get UserKeyMapping > captures/dials-mapping-during.txt
echo "Quick dial test (~25 s). Keep this pane focused."; for i in 5 4 3 2 1; do printf "\rstarting in %s " $i; sleep 1; done; echo
/Users/bob/repos/glra-studio/.venv/bin/python capture.py dials captures/${1:-4-dials}.jsonl
