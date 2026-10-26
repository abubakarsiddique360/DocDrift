"""Render a change report."""

from __future__ import annotations

from docdrift.diff import ADDED, EDITED, MOVED, REMOVED, DocDiff

SYMBOL = {ADDED: "＋", EDITED: "~", MOVED: "→", REMOVED: "−", "unchanged": "="}
LABEL = {ADDED: "added", EDITED: "edited", MOVED: "moved", REMOVED: "removed", "unchanged": "unchanged"}


def summary_line(diff: DocDiff) -> str:
    counts = diff.counts()
    parts = [f"{counts[kind]} {LABEL[kind]}" for kind in (ADDED, REMOVED, EDITED, MOVED)]
    parts.append(f"{counts['unchanged']} unchanged")
    return " · ".join(parts)


def render_markdown(diff: DocDiff, old_label: str = "old", new_label: str = "new") -> str:
    lines = [f"# Document drift: {old_label} → {new_label}", "", summary_line(diff), ""]

    for change in diff.changes:
        if change.kind == "unchanged":
            continue
        lines.append(f"## {SYMBOL.get(change.kind, '?')} {change.heading} — {LABEL[change.kind]}")
        if change.kind in {EDITED, MOVED}:
            lines.append("")
            lines.append(
                f"Similarity {change.similarity:.2f} · words {change.words_before} → {change.words_after}"
            )
        for sentence in change.added:
            lines.append(f"+ {sentence}")
        for sentence in change.removed:
            lines.append(f"- {sentence}")
        lines.append("")

    if diff.identical:
        lines.append("No changes: the documents are identical at section level.")
    return "\n".join(lines).rstrip() + "\n"


def render_table(diff: DocDiff) -> str:
    rows = [("KIND", "HEADING", "SIMILARITY", "WORDS")]
    for change in diff.changes:
        rows.append(
            (
                LABEL[change.kind].upper(),
                change.heading[:44],
                f"{change.similarity:.2f}",
                f"{change.words_before}→{change.words_after}",
            )
        )
    widths = [max(len(row[index]) for row in rows) for index in range(4)]
    lines = ["  ".join(cell.ljust(widths[index]) for index, cell in enumerate(rows[0]))]
    lines.append("-" * (sum(widths) + 6))
    for row in rows[1:]:
        lines.append("  ".join(cell.ljust(widths[index]) for index, cell in enumerate(row)))
    lines.append("")
    lines.append(summary_line(diff))
    if diff.identical:
        lines.append("Documents are identical at section level.")
    return "\n".join(lines)
