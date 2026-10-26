from __future__ import annotations

from pathlib import Path

from docdrift.diff import ADDED, EDITED, MOVED, REMOVED, UNCHANGED, compare
from docdrift.report import render_markdown, render_table, summary_line

EXAMPLES = Path(__file__).resolve().parent.parent / "examples"


def load_examples() -> tuple[str, str]:
    return (EXAMPLES / "old.md").read_text(encoding="utf-8"), (EXAMPLES / "new.md").read_text(encoding="utf-8")


def kinds(diff) -> dict[str, str]:
    return {change.heading: change.kind for change in diff.changes}


def test_identical_documents_produce_no_changes() -> None:
    text = "# Title\n\n## One\n\nHello there.\n\n## Two\n\nGoodbye.\n"
    diff = compare(text, text)
    assert diff.identical is True
    assert diff.counts()[UNCHANGED] == 3  # preamble-free: two sections + title section


def test_edited_section_is_detected_with_sentences() -> None:
    old = "## Intro\n\nAlpha beta gamma. Shared sentence here.\n"
    new = "## Intro\n\nAlpha beta gamma. Shared sentence here. A new sentence appears.\n"
    diff = compare(old, new)
    change = diff.changes[0]
    assert change.kind == EDITED
    assert "A new sentence appears." in change.added


def test_added_and_removed_sections() -> None:
    old = "## Keep\n\nShared body text here for matching.\n\n## Gone\n\nUnique removed body.\n"
    new = "## Keep\n\nShared body text here for matching.\n\n## Fresh\n\nA brand new section.\n"
    diff = compare(old, new)
    mapping = kinds(diff)
    assert mapping["Fresh"] == ADDED
    assert mapping["Gone"] == REMOVED


def test_moved_section_keeps_its_content() -> None:
    old = "## A\n\nShared body.\n\n## B\n\nUnique text about deployment rollbacks.\n"
    new = "## B\n\nUnique text about deployment rollbacks.\n\n## A\n\nShared body.\n"
    diff = compare(old, new)
    assert {change.kind for change in diff.changes} <= {UNCHANGED, MOVED}


def test_examples_have_every_change_kind() -> None:
    old, new = load_examples()
    diff = compare(old, new)
    counts = diff.counts()
    assert counts[EDITED] >= 2
    assert counts[UNCHANGED] >= 2
    assert counts[ADDED] == 1
    assert counts[REMOVED] == 1
    assert counts[MOVED] == 1  # Escalation was reordered without edits


def test_example_edited_section_lists_sentences() -> None:
    old, new = load_examples()
    diff = compare(old, new)
    on_call = next(change for change in diff.changes if change.heading == "On-call rotation")
    assert on_call.kind == EDITED
    assert any("09:00" in sentence for sentence in on_call.added)
    assert any("10:00" in sentence for sentence in on_call.removed)


def test_threshold_can_disable_move_matching() -> None:
    old = "## A\n\nSome medium length body about releases and rollbacks.\n"
    new = "## Z\n\nSome medium length body about releases and deployment windows.\n"
    assert compare(old, new, threshold=0.2).changes[0].kind in {MOVED, UNCHANGED}
    assert compare(old, new, threshold=0.99).changes[0].kind in {ADDED, REMOVED}


def test_as_dict_is_serialisable() -> None:
    old, new = load_examples()
    payload = compare(old, new).as_dict()
    assert payload["identical"] is False
    assert payload["counts"][ADDED] == 1
    assert isinstance(payload["words_added"], int)


def test_report_rendering() -> None:
    old, new = load_examples()
    diff = compare(old, new)
    markdown = render_markdown(diff, "old.md", "new.md")
    assert "# Document drift: old.md → new.md" in markdown
    assert "Cost controls" in markdown
    table = render_table(diff)
    assert "KIND" in table
    assert summary_line(diff).count("·") == 4
