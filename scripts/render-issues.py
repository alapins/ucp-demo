#!/usr/bin/env python3
"""Render the issue tracker's JSONL export as a document a person can read.

`bd export` writes one JSON object per line, which is the right shape for import
and diffing and the wrong shape for reading. This turns that file into Markdown,
nested the way the issues themselves are nested, so the spec and the tickets that
hang off it can be read in order without a tool.

    bd export -o .beads/issues.jsonl && python3 scripts/render-issues.py

The JSONL stays the source of truth: beads owns it and regenerates it, and this
reads it rather than the database, so the document can never disagree with the
export it came from.
"""

import json
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
EXPORT = ROOT / ".beads" / "issues.jsonl"
DOCUMENT = ROOT / "docs" / "issues.md"

STATUS_MARK = {
    "open": "○",
    "in_progress": "◐",
    "closed": "✓",
    "blocked": "●",
    "deferred": "❄",
}


def read_issues(path):
    if not path.exists():
        sys.exit(f"no export at {path} — run `bd export -o {path}` first")
    with path.open(encoding="utf-8") as lines:
        return [json.loads(line) for line in lines if line.strip()]


def parent_of(issue):
    """The issue this one hangs off, if any.

    Beads records hierarchy as a dependency like any other, distinguished by type,
    so a parent is found rather than read off a field.
    """
    for dependency in issue.get("dependencies") or []:
        if dependency.get("type") == "parent-child":
            return dependency.get("depends_on_id")
    return None


def blockers_of(issue):
    return [
        dependency["depends_on_id"]
        for dependency in issue.get("dependencies") or []
        if dependency.get("type") == "blocks"
    ]


def without_parent_section(text, parent):
    """Drop the `## Parent` block a ticket's description opens with.

    It names the id this issue hangs off, which the document already says by
    nesting the issue underneath it. Removed only when it agrees with the recorded
    dependency, so a description saying something unexpected is left to be read.
    """
    if not text or not parent:
        return text
    return re.sub(
        rf"\A#{{1,4}} Parent\s*\n+{re.escape(parent)}\s*\n+", "", text, count=1
    )


def demoted(text, by=3):
    """Push any Markdown headings inside a description below the ones around it.

    Descriptions carry their own `## Problem Statement` and the like. Left alone
    they would outrank the issue they belong to and break the document's outline.
    """
    if not text:
        return ""
    return re.sub(
        r"^(#{1,4}) ",
        lambda found: "#" * min(len(found.group(1)) + by, 6) + " ",
        text.strip(),
        flags=re.MULTILINE,
    )


def sort_key(issue):
    """Order as a human numbers them: 90m.2 before 90m.10."""
    return [
        int(part) if part.isdigit() else part
        for part in re.split(r"(\d+)", issue["id"])
    ]


def render_issue(issue, depth, out):
    heading = "#" * min(depth, 6)
    status = issue.get("status", "open")
    out.append(f"{heading} {STATUS_MARK.get(status, '·')} {issue['title']}")
    out.append("")

    facts = [
        f"`{issue['id']}`",
        status,
        f"P{issue.get('priority', '?')}",
        issue.get("issue_type", ""),
    ]
    labels = issue.get("labels") or []
    if labels:
        facts.append(" ".join(f"`{label}`" for label in labels))
    out.append(" · ".join(part for part in facts if part))
    out.append("")

    blockers = blockers_of(issue)
    if blockers:
        out.append(f"**Blocked by** {', '.join(f'`{b}`' for b in blockers)}")
        out.append("")

    description = without_parent_section(issue.get("description"), parent_of(issue))
    if description:
        out.append(demoted(description, by=depth))
        out.append("")

    if issue.get("acceptance_criteria"):
        out.append("**Acceptance criteria**")
        out.append("")
        out.append(issue["acceptance_criteria"].strip())
        out.append("")

    if issue.get("notes"):
        out.append("**Notes**")
        out.append("")
        out.append(issue["notes"].strip())
        out.append("")

    if issue.get("close_reason"):
        out.append(f"**Closed** — {issue['close_reason'].strip()}")
        out.append("")


def main():
    issues = read_issues(EXPORT)
    by_id = {issue["id"]: issue for issue in issues}
    children = {}
    roots = []
    for issue in sorted(issues, key=sort_key):
        parent = parent_of(issue)
        if parent and parent in by_id:
            children.setdefault(parent, []).append(issue)
        else:
            roots.append(issue)

    open_count = sum(1 for i in issues if i.get("status") != "closed")
    closed_count = len(issues) - open_count

    out = [
        "# Issues",
        "",
        "Generated from `.beads/issues.jsonl` by `scripts/render-issues.py`; edit"
        " issues with `bd`, not here. Regenerate with:",
        "",
        "```bash",
        "bd export -o .beads/issues.jsonl && python3 scripts/render-issues.py",
        "```",
        "",
        f"**{len(issues)} issues** — {open_count} open, {closed_count} closed.",
        "",
        "| | ID | Priority | Title |",
        "| --- | --- | --- | --- |",
    ]
    for issue in sorted(issues, key=sort_key):
        mark = STATUS_MARK.get(issue.get("status", "open"), "·")
        out.append(
            f"| {mark} | `{issue['id']}` | P{issue.get('priority', '?')} |"
            f" {issue['title']} |"
        )
    out.append("")
    out.append("○ open · ◐ in progress · ✓ closed · ● blocked · ❄ deferred")
    out.append("")

    for root in roots:
        out.append("---")
        out.append("")
        render_issue(root, depth=2, out=out)
        for child in children.get(root["id"], []):
            render_issue(child, depth=3, out=out)

    DOCUMENT.parent.mkdir(parents=True, exist_ok=True)
    DOCUMENT.write_text("\n".join(out).rstrip() + "\n", encoding="utf-8")
    print(f"wrote {DOCUMENT.relative_to(ROOT)} — {len(issues)} issues")


if __name__ == "__main__":
    main()
