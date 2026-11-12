# replug-leak-window: close the post-replug leak

Suggested model: Sonnet.

After a replug, macOS overwrites the pad's UserKeyMapping (it reapplies Bob's
modifier-key setting) shortly after we apply ours. The 2 s re-check restores it,
but on 2026-11-12 one key (Home) leaked in between (see `mvp-acceptance` results).
Re-check fast (e.g. every 100 ms) for the first ~10 s after each (re)connect,
then fall back to 2 s. Better still, find out whether delaying the first apply until
macOS has done its own (e.g. waiting for its entry to appear) removes the race.
Verify with Bob: replug, then immediately press keys 2/16 repeatedly for 5 s with the
runner pane focused; nothing may type. Also add README usage (install, run,
mapping, unsilence) if it's still missing.
