# Domain Docs

How the engineering skills should consume this repo's domain documentation.

## Before exploring, read these

- **`CONTEXT.md`** at the repo root — the domain glossary.
- **`docs/adr/`** — read ADRs that touch the area you're about to work in.

This is a **single-context** repo.

## Use the glossary's vocabulary

When output names a domain concept (issue title, proposal, hypothesis, test name), use the
term as defined in `CONTEXT.md`; don't drift to synonyms listed under `_Avoid_`.

## Flag ADR conflicts

If output contradicts an existing ADR, surface it explicitly rather than silently overriding.
