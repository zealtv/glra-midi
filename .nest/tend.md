# Tend

## Purpose

This nest receives material for glra-osc (briefs, notes, captures, links)
and routes each item to where it belongs in the repo.

## Recognise

- A Markdown file holding material, a request, or both.
- A directory with `request.md` and optional `attachments/`.
- A bare file (capture, screenshot, log) whose purpose comes from its name or
  from Bob; ask if it's unclear.

## Route

1. Claim with `./.nest/nestling.sh claim <name>` and read the whole item.
2. Source material worth keeping whole (briefs, specs, captures) →
   `./.lore/lore.sh keep` (`lore:<id>`).
3. Guidance that should change how future work is done → revise or add a
   glean finding (`glean:<id>`), then `./.glean/glean.sh index`.
4. Work it implies → stitches on the loom (`loom:<id>`). Plan only what Bob
   asked for. Don't widen scope from an item alone.
5. Hatch a receipt naming each route taken:
   `./.nest/nestling.sh complete <name> <receipt> <name>-receipt.md`.
   If nothing safe can be done, `drop` with a reason.

## Hard rules

- Briefs here are directions, not specifications; Bob's own words win
  (see `glean:brief-is-direction`).
- Never write to the pad (assignments, lighting) while tending; that belongs
  to a stitch Bob has confirmed.
- Don't overwrite existing lore items or findings; revise findings deliberately.

## Context

`AGENTS.md`, `.glean/findings/INDEX.md`, `./.loom/loom.sh status`.
