# Issue tracker: Beads (`bd`)

Issues and specs for this repo live in [beads](https://github.com/gastownhall/beads). Use the `bd` CLI for all operations.

Beads is a local-first tracker: issues live in a Dolt database under `.beads/`, sync travels over `refs/dolt/data` on the git remote, and `.beads/issues.jsonl` is a passive export. Do not hand-edit `.beads/issues.jsonl` — it is regenerated.

Issue IDs are `<prefix>-<suffix>`. This repo's `issue_prefix` is **`intuit-ucp`**, so IDs look like `intuit-ucp-a1b2`. Always pass full IDs; there are no bare `#42` numbers.

This repo has **no git remote** — beads is local-only here, and there is nothing to sync or push.

`CLAUDE.md` and `AGENTS.md` make beads the tracker for *all* task tracking in this repo and prohibit TodoWrite, TaskCreate, and markdown TODO files. That rule governs: never fall back to the `.scratch/<feature>/` markdown convention, even though other skills mention it as a default.

## Conventions

- **Create an issue**: `bd create --title "..." --description "..." --type=task|bug|feature|chore|epic --priority=2`.
  - Priority is `0`–`4` (`0` = critical, `2` = medium, `4` = backlog) — **not** `high`/`medium`/`low`.
  - For a multi-line body, pipe a heredoc into `--body-file -` (or `--stdin`) rather than fighting shell quoting.
  - `--labels a,b` sets labels at creation; `--deps <blocker-id>` wires blockers in the same command.
  - `--parent <id>` makes it a hierarchical child (child IDs nest: `<parent>.1`, `.2`, …). **Children inherit the parent's labels** — pass `--no-inherit-labels` whenever the parent carries a label that must not spread, such as a marker label identifying the parent itself.
  - `--acceptance "..."`, `--design "..."`, `--notes "..."` populate the structured fields; `--validate` checks the description has the sections the type requires.
  - `--silent` prints only the new ID — use it when scripting a batch so you can capture IDs for dependency wiring.
- **Read an issue**: `bd show <id>` (add `--long` for all fields, `--json` for machine-readable). Comments are separate: `bd comments <id>`.
- **List issues**: `bd list --status=open` with `--label`, `--label-any`, `--exclude-label`, `--parent`, `--assignee` filters; `--json` for machine-readable output. `bd search <query>` for full-text.
- **Comment on an issue**: `bd comment <id> "..."`, or `bd comment <id> --file notes.md` / `--stdin` for long bodies. (`bd note <id> "..."` appends to the issue's *notes field* instead — a different thing from a comment.)
- **Apply / remove labels**: `bd label add <id> <label>` / `bd label remove <id> <label>`. `bd tag <id> <label>` is shorthand for adding one.
- **Update fields**: `bd update <id> --title/--description/--notes/--design/--acceptance/--priority`. `bd update <id> --claim` atomically claims (assignee = you, status = `in_progress`).
- **Close**: `bd close <id> --reason "..."`. Close several at once: `bd close <id1> <id2> ...`. `--suggest-next` reports what the close just unblocked.

**Never run `bd edit`** — it opens `$EDITOR` and blocks the agent. Use `bd update` with inline flags.

## Blocking is native

This is the reason to prefer beads over a file-based tracker for `/to-tickets` and `/wayfinder`: blocking edges are first-class, queryable, and cycle-checked.

- **Add an edge**: `bd dep add <blocked-id> <blocker-id>` — "blocked depends on blocker". The mirror form `bd dep <blocker-id> --blocks <blocked-id>` reads better when wiring forward.
- **Inspect**: `bd dep list <id>`, `bd dep tree <id>`, `bd graph`. `bd dep cycles` detects cycles.
- **Remove**: `bd dep remove <blocked-id> <blocker-id>`.
- **Frontier**: `bd ready` — open issues with no *active* blockers, excluding `in_progress`, `blocked`, and `deferred`. This is the canonical "what can start now" query; `--explain` shows the reasoning, `--json` makes it parseable.
- **The other side**: `bd blocked` lists everything currently gated.

Because blockers are real edges, a ticket body should **not** carry a prose "Blocked by" list — it would drift from the graph. Record blocking only with `bd dep`.

## Pull requests as a triage surface

**PRs as a request surface: no.** _(`/triage` reads this flag.)_

Beads has no PR surface of its own. If this repo takes external PRs and you want them in the triage queue, set the flag to `yes` and read them with `gh pr` / `glab mr` while keeping all triage *state* in beads — mirror each PR as an issue whose `--external-ref` points at it (e.g. `--external-ref gh-42`), and label that issue.

## When a skill says "publish to the issue tracker"

Run `bd create`. Publish in dependency order (blockers first) so each ticket can be wired with `bd dep add` — or `--deps` at creation — against a real ID.

Specs (`/to-spec`) are issues too: `bd create --type=feature --title "<feature>" --body-file -` with the spec as the description, labelled `ready-for-agent`. Implementation tickets from `/to-tickets` then hang off it with `--parent <spec-id>`.

## When a skill says "fetch the relevant ticket"

Run `bd show <id>` followed by `bd comments <id>`. The user will normally pass the ID directly.

## Wayfinding operations

Used by `/wayfinder`. The **map** is an epic bead; its **tickets** are child beads.

- **Map**: `bd create --type=epic --labels wayfinder:map --title "<effort>" --body-file -`, holding the Notes / Decisions-so-far / Fog body. Update it with `bd update <map-id> --body-file -`.
- **Child ticket**: `bd create --parent <map-id> --no-inherit-labels --labels wayfinder:<type> --title "<question>" --body-file -`, where `<type>` is `research`/`prototype`/`grilling`/`task`.
  - **`--no-inherit-labels` is required.** Children inherit the parent's labels by default, so without it every ticket comes out labelled `wayfinder:map` and the map is no longer identifiable by its label.
  - Child IDs nest under the parent (`<map-id>.1`, `.2`, …), so the map membership is visible in the ID itself. List them with `bd children <map-id>`.
- **Blocking**: `bd dep add <child-id> <blocker-id>` — native edges, no prose line. A ticket is unblocked when every blocker is closed.
- **Frontier query**: `bd ready --parent <map-id> --exclude-type=epic`. `--parent` scopes to the map's descendants; `--exclude-type=epic` drops the map itself, which otherwise shows up as ready work. It already excludes blocked, claimed, and deferred tickets; first in map order wins.
- **Claim**: `bd update <id> --claim` — the session's first write. (`bd ready --claim` atomically claims the first ready ticket in one step.)
- **Resolve**: `bd comment <id> "<answer>"`, then `bd close <id> --reason "<gist>"`, then append a context pointer (gist + ID) to the map's Decisions-so-far.

## Triage queries

`/triage` needs an "unlabeled" bucket. Beads has no negative-label query, so express it as an exclusion of the whole vocabulary:

```bash
bd list --status=open --exclude-label=needs-triage,needs-info,ready-for-agent,ready-for-human,wontfix
```

The other two buckets are `bd list --status=open --label=needs-triage` and `bd list --status=open --label=needs-info` (check the latter for reporter replies with `bd comments <id>`). Sort oldest-first with `--created-before` filters or by reading `created` from `--json`.

## Sync and git authority

Beads writes to a local Dolt database, so creating and closing issues is **not** a git operation and needs no push authority. With no remote configured here, there is no sync step at all. The repo's git policy in `CLAUDE.md` still governs: do not commit or push unless explicitly asked.
