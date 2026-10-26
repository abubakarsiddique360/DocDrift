# DocDrift

**Two versions of a document in. Every change out — edited, moved, added, removed, unchanged.**

A line diff tells you that 40 lines changed. That is rarely the question. When a
policy, a spec or a runbook is revised, the questions are: *which claims were
edited, which section disappeared, and did anything move without being rewritten?*
DocDrift answers at section level and, for edits, at sentence level.

[![CI](https://github.com/abubakarsiddique360/DocDrift/actions/workflows/ci.yml/badge.svg)](https://github.com/abubakarsiddique360/DocDrift/actions/workflows/ci.yml)
[![Python](https://img.shields.io/badge/python-3.10%20%7C%203.12-blue)](pyproject.toml)
[![License](https://img.shields.io/badge/license-MIT-green)](LICENSE)
[![Dependencies](https://img.shields.io/badge/dependencies-none-brightgreen)](pyproject.toml)

## Quick start

```bash
git clone https://github.com/abubakarsiddique360/DocDrift.git
cd DocDrift
python -m venv .venv
# Windows: .venv\Scripts\activate     macOS/Linux: source .venv/bin/activate
pip install -e ".[dev]"

docdrift diff examples/old.md examples/new.md
docdrift diff examples/old.md examples/new.md --markdown -o drift.md
```

```
KIND       HEADING                  SIMILARITY  WORDS
-----------------------------------------------------
UNCHANGED  Runtime incident policy  1.00        0→0
UNCHANGED  Severity levels          1.00        19→19
EDITED     Purpose                 0.75        23→30
EDITED     On-call rotation        0.45        22→27
MOVED      Escalation              1.00        22→22
ADDED      Cost controls           1.00        0→18
REMOVED    Appendix: history       1.00        10→0

1 added · 1 removed · 2 edited · 1 moved · 2 unchanged
```

The markdown report adds the sentence-level detail for each edited section:

```markdown
## ~ On-call rotation — edited

Similarity 0.45 · words 22 → 27
+ The rotation runs weekly and changes on Monday at 09:00.
- The rotation runs weekly and changes on Monday at 10:00.
```

## The five change kinds

| Kind | Meaning | How it is decided |
| --- | --- | --- |
| `unchanged` | same heading, same body | exact normalised match |
| `edited` | same heading, different body | heading match + sentence comparison |
| `moved` | same content, different position (or different heading) | order analysis / shingle similarity ≥ threshold |
| `added` | a section that did not exist | no match in the old document |
| `removed` | a section that no longer exists | no match in the new document |

**How moves are detected.** Sections matched by heading keep their identity, so a
pure reorder would look unchanged. DocDrift compares the sequence of matched
sections with the longest increasing subsequence of their old positions: anything
outside that subsequence was displaced, and unchanged content that moved is
reported as `moved`. Sections that are already `edited` are not double-labelled.

**How renames are detected.** Content is fingerprinted with 3-word shingles and
compared with Jaccard similarity; a section that keeps most of its shingles but
gets a new heading is reported as `moved` with its similarity score.

## Why not just `git diff`?

- Grouping: a diff is per line; DocDrift is per heading, which maps to how review is
  actually assigned and discussed.
- Classification: "this block of 40 lines changed" becomes "the purpose gained one
  sentence, the on-call section changed its handover time".
- Gates: `--fail-on-removed` turns "nobody noticed the appendix was deleted" into a
  failing check in CI.

## CLI

| Command | Purpose |
| --- | --- |
| `diff OLD NEW` | Table of sections and their change kind |
| `diff OLD NEW --markdown [-o out.md]` | Full report with added/removed sentences |
| `diff OLD NEW --json` | Machine-readable diff |
| `diff OLD NEW --fail-on-removed` | Exit `1` when a section disappeared |
| `diff OLD NEW --threshold 0.7` | Raise the similarity needed for a move match |

Exit codes: `0` compared, `1` a removal was found and `--fail-on-removed` was set,
`2` a file could not be read.

## Project layout

```text
src/docdrift/
├── parse.py     heading sections, sentences, word shingles
├── diff.py      matching, classification, move detection
├── report.py    table + markdown rendering
└── cli.py       diff (table · markdown · json)
examples/        an incident policy, before and after
tests/           26 pytest cases
```

## Design notes

- **Sections are the unit.** Headings are how documents are written and reviewed, so
  they are the natural unit of a change report.
- **Deterministic, dependency-free.** No model, no embeddings: word shingles and set
  overlap. The same two files always produce the same report.
- **Sentence-level detail only where it matters.** Unchanged and moved sections stay
  one line long; only edited sections are expanded.
- **Conservative move detection.** Two sections with different content are never
  called a move; they are an add plus a remove, which is the safer reading.

## Limitations

- Markdown headings are the structure. A document without headings is treated as one
  section, so the report collapses to a single edited/unchanged verdict.
- Shingle similarity ignores meaning: a paragraph that is rewritten in different
  words counts as an edit, not a move.
- No inline formatting diff (bold, links) and no table-cell diff.
- PDFs and Word files are not supported; convert to text or markdown first.

## License

[MIT](LICENSE) © 2026 **ABU BAKAR SIDDIQUE**
