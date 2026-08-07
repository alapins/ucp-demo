#!/usr/bin/env bash
# Re-apply this repo's local overlay onto the apm-managed mattpocock skills.
#
# apm.yml pulls mattpocock/skills from the default branch, unpinned, so
# `apm install` overwrites everything under .agents/skills/. This script puts
# our additions back. It is idempotent — safe to run any time.
#
#   docs/agents/upstream-overlay/apply.sh
#
# See README.md in this directory for what it changes and why.

set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
overlay="$repo_root/docs/agents/upstream-overlay"
skill_dir="$repo_root/.agents/skills/setup-matt-pocock-skills"

if [[ ! -d "$skill_dir" ]]; then
  echo "error: $skill_dir not found — run 'apm install' first" >&2
  exit 1
fi

# 1. The new seed template (a file upstream doesn't have; a plain copy suffices).
cp -f "$overlay/setup-matt-pocock-skills/issue-tracker-beads.md" "$skill_dir/issue-tracker-beads.md"
echo "✓ issue-tracker-beads.md"

# 2. Two insertions into the upstream SKILL.md. Anchored on upstream text; if an
#    anchor is gone, upstream restructured that section — reapply by hand.
python3 - "$skill_dir/SKILL.md" <<'PY'
import sys

path = sys.argv[1]
src = open(path).read()

INSERTIONS = [
    (
        "Section A tracker option",
        "- **Local markdown** — issues live as files under `.scratch/",
        "- **Beads** — issues live in a local [beads](https://github.com/gastownhall/beads) "
        "database (uses the `bd` CLI). Propose this if a `.beads/` directory exists, or if "
        "`CLAUDE.md` / `AGENTS.md` already names `bd` as the tracker — it has native blocking "
        "edges, so `/to-tickets` and `/wayfinder` get real dependency graphs instead of prose "
        '"Blocked by" lines\n',
    ),
    (
        "template list entry",
        "- [issue-tracker-local.md](./issue-tracker-local.md)",
        "- [issue-tracker-beads.md](./issue-tracker-beads.md) — beads (`bd`) issue tracker\n",
    ),
]

changed = False
for label, anchor, addition in INSERTIONS:
    if addition.strip() in src:
        print(f"  = {label} (already present)")
        continue
    if anchor not in src:
        print(f"  ! {label}: anchor missing — upstream changed; reapply by hand", file=sys.stderr)
        sys.exit(1)
    i = src.index(anchor)
    src = src[:i] + addition + src[i:]
    changed = True
    print(f"  + {label}")

if changed:
    open(path, "w").write(src)
print("✓ SKILL.md")
PY
