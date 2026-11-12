#!/bin/zsh
# Hands-on silence + MIDI check (2026-11-12). Runs `glra-osc run --dry-run` in the
# background, walks Bob through all 25 controls in this focused pane (keystroke leaks
# land here and get logged; volume/mute is sampled around dial steps), then
# stops the runner and checks the pad's original hidutil mapping is back.
cd "${0:A:h}"; R=/Users/bob/repos/glra-osc; CAP=$R/.loom/threads/midi-mvp/raw-report-capture.tied
M='{"VendorID":0x36ae,"ProductID":0x2475}'
mkdir -p checks; STAMP=$(date +%H%M%S)
hidutil property --matching "$M" --get UserKeyMapping > checks/$STAMP-mapping-before.txt
$R/.venv/bin/glra-osc run --dry-run > checks/$STAMP-run.log 2>&1 &
RUN=$!; sleep 3
hidutil property --matching "$M" --get UserKeyMapping > checks/$STAMP-mapping-during.txt
echo "runner pid $RUN; mapping entries during: $(grep -c Src checks/$STAMP-mapping-during.txt)"
for i in 5 4 3 2 1; do printf "\rstarting in %s " $i; sleep 1; done; echo
/Users/bob/repos/glra-studio/.venv/bin/python $CAP/capture.py allcontrols checks/$STAMP-capture.jsonl
kill -TERM $RUN; wait $RUN; echo "runner exit: $?"
sleep 1; hidutil property --matching "$M" --get UserKeyMapping > checks/$STAMP-mapping-after.txt
echo "mapping entries after: $(grep -c Src checks/$STAMP-mapping-after.txt) (before: $(grep -c Src checks/$STAMP-mapping-before.txt))"
echo $STAMP > checks/latest
