"""Compare two document versions section by section."""

from __future__ import annotations

from dataclasses import dataclass, field

from docdrift.parse import Section, changed_sentences, jaccard, split_sections, word_count

UNCHANGED = "unchanged"
EDITED = "edited"
MOVED = "moved"
ADDED = "added"
REMOVED = "removed"
KINDS = (UNCHANGED, EDITED, MOVED, ADDED, REMOVED)

DEFAULT_THRESHOLD = 0.5


@dataclass(frozen=True)
class SectionChange:
    kind: str
    heading: str
    similarity: float = 1.0
    added: tuple[str, ...] = ()
    removed: tuple[str, ...] = ()
    words_before: int = 0
    words_after: int = 0

    def as_dict(self) -> dict:
        return {
            "kind": self.kind,
            "heading": self.heading,
            "similarity": round(self.similarity, 3),
            "added_sentences": list(self.added),
            "removed_sentences": list(self.removed),
            "words_before": self.words_before,
            "words_after": self.words_after,
        }


@dataclass
class DocDiff:
    changes: list[SectionChange] = field(default_factory=list)

    def counts(self) -> dict[str, int]:
        counts = dict.fromkeys(KINDS, 0)
        for change in self.changes:
            counts[change.kind] += 1
        return counts

    @property
    def removed(self) -> list[SectionChange]:
        return [change for change in self.changes if change.kind == REMOVED]

    @property
    def added(self) -> list[SectionChange]:
        return [change for change in self.changes if change.kind == ADDED]

    @property
    def identical(self) -> bool:
        return all(change.kind == UNCHANGED for change in self.changes)

    def as_dict(self) -> dict:
        return {
            "identical": self.identical,
            "counts": self.counts(),
            "words_added": sum(
                change.words_after - change.words_before for change in self.changes if change.kind != UNCHANGED
            ),
            "changes": [change.as_dict() for change in self.changes],
        }


def _fingerprint(section: Section) -> str:
    return section.normalized_body


def compare(old_markdown: str, new_markdown: str, threshold: float = DEFAULT_THRESHOLD) -> DocDiff:
    old_sections = split_sections(old_markdown)
    new_sections = split_sections(new_markdown)

    old_used: set[int] = set()
    new_used: set[int] = set()
    changes: list[SectionChange] = []
    pairs: list[tuple[int, int]] = []

    # pass 1: same heading text
    for new_index, new_section in enumerate(new_sections):
        for old_index, old_section in enumerate(old_sections):
            if old_index in old_used:
                continue
            if old_section.heading.strip().lower() != new_section.heading.strip().lower():
                continue
            old_used.add(old_index)
            new_used.add(new_index)
            changes.append(_compare_pair(old_section, new_section, EDITED))
            pairs.append((changes.index(changes[-1]), old_index))
            break

    # pass 2: content moved under a different heading
    for new_index, new_section in enumerate(new_sections):
        if new_index in new_used:
            continue
        best_index, best_score = -1, 0.0
        for old_index, old_section in enumerate(old_sections):
            if old_index in old_used:
                continue
            score = jaccard(old_section.shingles(), new_section.shingles())
            if score > best_score:
                best_index, best_score = old_index, score
        if best_index >= 0 and best_score >= threshold:
            old_used.add(best_index)
            new_used.add(new_index)
            kind = UNCHANGED if _fingerprint(old_sections[best_index]) == _fingerprint(new_section) else MOVED
            changes.append(_compare_pair(old_sections[best_index], new_section, kind))
            pairs.append((len(changes) - 1, best_index))
        else:
            new_used.add(new_index)
            changes.append(
                SectionChange(
                    kind=ADDED,
                    heading=new_section.heading,
                    words_after=word_count(new_section.body),
                )
            )

    for old_index, old_section in enumerate(old_sections):
        if old_index in old_used:
            continue
        changes.append(
            SectionChange(
                kind=REMOVED,
                heading=old_section.heading,
                words_before=word_count(old_section.body),
            )
        )

    _mark_reordered(changes, pairs)

    order = {kind: index for index, kind in enumerate(KINDS)}
    changes.sort(key=lambda change: order[change.kind])
    return DocDiff(changes=changes)


def _mark_reordered(changes: list[SectionChange], pairs: list[tuple[int, int]]) -> None:
    """A section whose relative order changed is a move, even if nobody edited it.

    The longest increasing subsequence of old positions is treated as "stayed put";
    anything outside it was displaced.
    """

    ordered = sorted(pairs)
    sequence = [old_index for _, old_index in ordered]
    if sequence == sorted(sequence):
        return
    stable = _lis_positions(sequence)
    for position, (change_index, _) in enumerate(ordered):
        change = changes[change_index]
        if position in stable or change.kind != UNCHANGED:
            continue
        changes[change_index] = SectionChange(
            kind=MOVED,
            heading=change.heading,
            similarity=change.similarity,
            added=change.added,
            removed=change.removed,
            words_before=change.words_before,
            words_after=change.words_after,
        )


def _lis_positions(sequence: list[int]) -> set[int]:
    if not sequence:
        return set()
    length = [1] * len(sequence)
    previous = [-1] * len(sequence)
    for i, value in enumerate(sequence):
        for j in range(i):
            if sequence[j] < value and length[j] + 1 > length[i]:
                length[i] = length[j] + 1
                previous[i] = j
    cursor = max(range(len(sequence)), key=lambda index: length[index])
    keep: set[int] = set()
    while cursor >= 0:
        keep.add(cursor)
        cursor = previous[cursor]
    return keep


def _compare_pair(old: Section, new: Section, changed_kind: str) -> SectionChange:
    same_body = _fingerprint(old) == _fingerprint(new)
    similarity = jaccard(old.shingles(), new.shingles())
    if same_body and changed_kind != MOVED:
        return SectionChange(
            kind=UNCHANGED,
            heading=new.heading,
            similarity=1.0,
            words_before=word_count(old.body),
            words_after=word_count(new.body),
        )
    added, removed = changed_sentences(old.body, new.body)
    kind = MOVED if changed_kind == MOVED else EDITED
    if same_body:
        kind = MOVED
    return SectionChange(
        kind=kind,
        heading=new.heading,
        similarity=round(similarity, 3),
        added=tuple(added),
        removed=tuple(removed),
        words_before=word_count(old.body),
        words_after=word_count(new.body),
    )
