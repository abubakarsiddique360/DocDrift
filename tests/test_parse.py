from __future__ import annotations

from docdrift.parse import changed_sentences, jaccard, split_sections, word_count

DOC = """Intro text before any heading.

## First

Alpha beta gamma. Delta epsilon.

## Second

Zeta eta theta.
"""


def test_split_sections_includes_preamble() -> None:
    sections = split_sections(DOC)
    assert [section.heading for section in sections] == ["Preamble", "First", "Second"]
    assert sections[0].level == 0
    assert sections[1].level == 2


def test_split_sections_without_headings() -> None:
    sections = split_sections("Just a paragraph.")
    assert len(sections) == 1
    assert sections[0].heading == "Preamble"


def test_empty_document_has_no_sections() -> None:
    assert split_sections("   \n\n") == []


def test_sentences_are_split() -> None:
    sections = split_sections(DOC)
    assert sections[1].sentences() == ["Alpha beta gamma.", "Delta epsilon."]


def test_shingles_are_lowercased_tuples() -> None:
    section = split_sections(DOC)[1]
    shingles = section.shingles(size=2)
    assert ("alpha", "beta") in shingles


def test_short_section_shingles() -> None:
    section = split_sections("## H\n\none")[0]
    assert section.shingles(size=5) == {("one",)}


def test_jaccard_bounds() -> None:
    assert jaccard({("a",)}, {("a",)}) == 1.0
    assert jaccard({("a",)}, {("b",)}) == 0.0
    assert jaccard(set(), set()) == 1.0
    assert jaccard({("a",)}, set()) == 0.0


def test_word_count() -> None:
    assert word_count("one two three") == 3


def test_changed_sentences_reports_both_directions() -> None:
    added, removed = changed_sentences("Keep this. Drop that.", "Keep this. Add this.")
    assert added == ["Add this."]
    assert removed == ["Drop that."]
