"""Command-line interface for DocDrift."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from docdrift import __version__
from docdrift.diff import compare
from docdrift.report import render_markdown, render_table


def _read(path: str) -> str:
    return Path(path).read_text(encoding="utf-8")


def _diff(args: argparse.Namespace) -> int:
    old_text = _read(args.old)
    new_text = _read(args.new)
    diff = compare(old_text, new_text, threshold=args.threshold)

    if args.json:
        print(json.dumps(diff.as_dict(), indent=2))
    elif args.markdown or args.out:
        markdown = render_markdown(diff, Path(args.old).name, Path(args.new).name)
        if args.out:
            Path(args.out).write_text(markdown, encoding="utf-8")
            print(f"wrote {args.out}")
        else:
            print(markdown)
    else:
        print(render_table(diff))

    if args.fail_on_removed and diff.removed:
        return 1
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="docdrift",
        description="Compare two versions of a document and classify what changed.",
    )
    parser.add_argument("--version", action="version", version=f"docdrift {__version__}")
    sub = parser.add_subparsers(dest="command", required=True)

    diff = sub.add_parser("diff", help="compare two markdown/text documents")
    diff.add_argument("old")
    diff.add_argument("new")
    diff.add_argument(
        "--threshold", type=float, default=0.5, help="similarity needed to treat a section as moved"
    )
    diff.add_argument("--json", action="store_true")
    diff.add_argument("--markdown", action="store_true", help="print a markdown report")
    diff.add_argument("-o", "--out", help="write the markdown report to a file")
    diff.add_argument("--fail-on-removed", action="store_true", help="exit 1 when a section disappeared")
    diff.set_defaults(func=_diff)
    return parser


def main(argv: list[str] | None = None) -> int:
    for stream in (sys.stdout, sys.stderr):
        reconfigure = getattr(stream, "reconfigure", None)
        if reconfigure is not None:
            reconfigure(encoding="utf-8", errors="replace")
    args = build_parser().parse_args(argv)
    try:
        return int(args.func(args))
    except FileNotFoundError as exc:
        print(f"error: file not found: {exc.filename}", file=sys.stderr)
        return 2
    except OSError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
