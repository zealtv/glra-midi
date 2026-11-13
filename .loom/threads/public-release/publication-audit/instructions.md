# publication-audit — what the whole history makes public

Bob, 2026-11-13: audit first, then the existing repo goes public with full
history; "i'd like the research done here to be public". So the research
(.loom, .lore, .glean, .nest) stays. This stitch reads the tree and every
commit (`git log -p --all`, including binaries' names and sizes) and reports;
it changes nothing in history.

Look for: credentials, tokens or keys; personal details beyond Bob's name and
commit email (addresses, phone numbers, other people's details, private
messages); third-party material we may not have the right to republish (vendor
firmware dumps or flash images, datasheets, other people's photos, copied web
pages); paths or notes about other private projects; anything the GPL needs
that's missing (SPDX headers, notices, attribution to glra-studio). Note large
files too.

Write `audit.md`: each finding, the commits and paths it touches, and options
(remove from the tree only, rewrite history, accept). History rewrites and the
choice of what stays are Bob's. Fixes that only touch the current tree and are
clearly right (a missing header) can land here.
