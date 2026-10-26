"""Split a document into comparable sections and sentences."""

from __future__ import annotations

import re
from dataclasses import dataclass

_HEADING_RE = re.compile(r"^(#{1,6})\s+(.*)$", re.MULTILINE)
_SENTENCE_RE = re.compile(r"(?<=[.!?])\s+")
_WORD_RE = re.compile(r"[A-Za-z0-9][A-Za-z0-9'\-]*")


@dataclass(frozen=True)
class Section:
    heading: str
    level: int
    body: str

    @property
    def normalized_body(self) -> str:
        return " ".join(self.body.split()).lower()

    def sentences(self) -> list[str]:
        return [part.strip() for part in _SENTENCE_RE.split(" ".join(self.body.split())) if part.strip()]

    def shingles(self, size: int = 3) -> set[tuple[str, ...]]:
        words = [word.lower() for word in _WORD_RE.findall(self.body)]
        if len(words) < size:
            return {tuple(words)} if words else set()
        return {tuple(words[index : index + size]) for index in range(len(words) - size + 1)}


def word_count(text: str) -> int:
    return len(_WORD_RE.findall(text))


def split_sections(markdown: str) -> list[Section]:
    """Heading-delimited sections; text before the first heading becomes 'Preamble'."""

    matches = list(_HEADING_RE.finditer(markdown))
    if not matches:
        body = markdown.strip()
        return [Section("Preamble", 0, body)] if body else []

    sections: list[Section] = []
    preamble = markdown[: matches[0].start()].strip()
    if preamble:
        sections.append(Section("Preamble", 0, preamble))

    for index, match in enumerate(matches):
        start = match.end()
        end = matches[index + 1].start() if index + 1 < len(matches) else len(markdown)
        sections.append(
            Section(
                heading=match.group(2).strip(),
                level=len(match.group(1)),
                body=markdown[start:end].strip(),
            )
        )
    return sections


def jaccard(left: set[tuple[str, ...]], right: set[tuple[str, ...]]) -> float:
    if not left and not right:
        return 1.0
    if not left or not right:
        return 0.0
    return len(left & right) / len(left | right)


def changed_sentences(old: str, new: str) -> tuple[list[str], list[str]]:
    """Sentence-level added/removed lists, in document order."""

    old_sentences = [part.strip() for part in _SENTENCE_RE.split(" ".join(old.split())) if part.strip()]
    new_sentences = [part.strip() for part in _SENTENCE_RE.split(" ".join(new.split())) if part.strip()]
    new_set = {" ".join(sentence.lower().split()) for sentence in new_sentences}
    old_set = {" ".join(sentence.lower().split()) for sentence in old_sentences}
    added = [sentence for sentence in new_sentences if " ".join(sentence.lower().split()) not in old_set]
    removed = [sentence for sentence in old_sentences if " ".join(sentence.lower().split()) not in new_set]
    return added, removed
