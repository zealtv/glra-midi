# Tend

Replace the prompts below with the host folder's policy. This file guides the
person or process tending this nest; Nestlings does not enforce it.

Keep only stable, operational directions needed to route an item. Link to
project context or agent instructions instead of copying either into this file.

## Purpose

State in one sentence what this nest receives and what tending should achieve.

## Recognise

List accepted item shapes and where intent is found. For example:

* a Markdown file containing both material and a request;
* a directory with `request.md` and optional `attachments/`.

## Route

When it is time to tend a batch:

1. Select an available item and claim it with `nestling.sh claim`.
2. Read the whole item, including its request and referenced attachments.
3. Take each applicable route below in the stated order.
4. Hatch a result or receipt with `nestling.sh complete`; if no safe route can
   be completed, use `nestling.sh drop` with a useful reason.

Replace this paragraph with concrete condition → action routes. A
single-purpose nest may need only one route. A repository-entry nest may route
to several local tools and then hatch one receipt recording what went where.

## Hard rules

List actions a tender must never take, even when an item asks. Keep expensive
trust decisions explicit. For example:

* Do not send messages or change external state without the required approval.
* Do not overwrite an existing destination.
* Do not invent missing material or intent.

## Context

Link only the sources a tender should consult, such as a project guide, current
memory, or destination conventions. Context remains in its owning files; this
policy says when to read it, not what it should contain.
