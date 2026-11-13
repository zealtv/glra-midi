# publication-audit — questions for Bob

Claude, 2026-11-13. Each has a default taken so `rename-places` and
`first-release` aren't blocked; none needs a history rewrite unless Bob says so.
Details in `audit.md`.

1. **The primitives' licence (F5).** `glean.sh`, `loom.sh`, `lore.sh`,
   `nestling.sh`, `groundhog.sh` carry no licence here, so in a GPL-3.0-only
   repo they read as GPL-3.0-only. Fine, or should `THIRD_PARTY_NOTICES.md`
   name their `zealtv/*` upstreams and own licence?
   *Default taken:* nothing changed.

2. **`zealtv/*` links (F4).** The dotdir READMEs link
   `github.com/zealtv/{glean,loom,nestlings,groundhog}`. Are those repos
   public? If not, readers will meet 404s (no leak).
   *Default taken:* links left as they are.

3. **Crash report identifiers (F1).** Accept `crashReporterKey` and
   `deviceIdentifierForVendor` in `quit-crash-184200.ips`, or redact (tree
   only, or history)?
   *Default taken:* accepted; nothing changed.

4. **Masses Chip's phone and email (F2).** Lore keeps them, so publishing
   publishes them, whatever `call-for-chip-info`'s doc does. Accept?
   *Default taken:* accepted; nothing changed.

5. **Any history rewrite at all?** Claude found nothing that needs one. If
   Bob wants F1 or F3 (`Claude-Session:` trailers) gone, a single
   `git filter-repo` pass before the first push would do both; every commit
   hash changes, and open worktrees/branches would need recreating.
   *Default taken:* no rewrite.
