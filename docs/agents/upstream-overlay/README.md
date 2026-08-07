# Upstream overlay

Local additions to the **apm-managed** skills under `.agents/skills/`.

`apm.yml` pulls `mattpocock/skills` from the default branch, unpinned (see the PINS
note at the top of `apm.yml`). So `apm install` overwrites `.agents/skills/` wholesale
and any edit made there is lost. This directory is the durable copy; `apply.sh` puts
it back.

```bash
docs/agents/upstream-overlay/apply.sh   # idempotent — run after any apm install/update
```

## What it adds

A **beads (`bd`) issue tracker** option for `/setup-matt-pocock-skills`. Upstream ships
three trackers — GitHub, GitLab, local markdown — and a freeform "Other" escape hatch.
This repo tracks work in beads, and beads has native, queryable blocking edges, which
`/to-tickets` and `/wayfinder` both want: upstream's local-markdown option degrades
them to prose `Blocked by:` lines.

Two changes, both to `setup-matt-pocock-skills`:

| Change | File | Kind |
| --- | --- | --- |
| The beads seed template | `issue-tracker-beads.md` | New file (no upstream conflict) |
| Beads as a Section A option | `SKILL.md` | Insertion before the local-markdown bullet |
| Beads in the seed-template list | `SKILL.md` | Insertion before the local-markdown entry |

`apply.sh` anchors its two `SKILL.md` insertions on upstream text. If upstream
restructures that section the anchors stop matching and the script fails loudly
rather than corrupting the file — reapply by hand, then update the anchors here.

## What it does NOT cover

This repo's own generated config — `docs/agents/issue-tracker.md`,
`triage-labels.md`, `domain.md`, and the `## Agent skills` blocks in `CLAUDE.md` and
`AGENTS.md` — lives outside `.agents/` and is never touched by apm. Nothing to restore.

Note that `docs/agents/issue-tracker.md` was seeded from the beads template and then
specialised for this repo (issue prefix `intuit-ucp`, a Dolt database that syncs
nowhere, `.scratch/` ruled out, a triage-query section). Re-running `apply.sh` does
not overwrite it. If you
improve the template here, port the change across deliberately.

## Upstreaming

The cleaner long-term fix is a PR adding `issue-tracker-beads.md` to
`mattpocock/skills`. If that lands, drop this overlay and pin the skill to a ref
that includes it.
