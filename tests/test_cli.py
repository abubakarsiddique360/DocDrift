from __future__ import annotations

import json
from pathlib import Path

from docdrift.cli import main

EXAMPLES = Path(__file__).resolve().parent.parent / "examples"
OLD = str(EXAMPLES / "old.md")
NEW = str(EXAMPLES / "new.md")


def test_table_output(capsys) -> None:
    assert main(["diff", OLD, NEW]) == 0
    out = capsys.readouterr().out
    assert "KIND" in out
    assert "EDITED" in out
    assert "unchanged" in out


def test_json_output(capsys) -> None:
    assert main(["diff", OLD, NEW, "--json"]) == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["identical"] is False
    assert payload["counts"]["added"] == 1
    assert payload["counts"]["removed"] == 1


def test_markdown_output(capsys) -> None:
    assert main(["diff", OLD, NEW, "--markdown"]) == 0
    out = capsys.readouterr().out
    assert out.startswith("# Document drift")
    assert "Cost controls" in out


def test_markdown_to_file(tmp_path, capsys) -> None:
    out_path = tmp_path / "report.md"
    assert main(["diff", OLD, NEW, "-o", str(out_path)]) == 0
    assert out_path.exists()
    assert "Chip" not in out_path.read_text(encoding="utf-8")
    assert "wrote" in capsys.readouterr().out


def test_identical_documents(capsys) -> None:
    assert main(["diff", OLD, OLD]) == 0
    assert "identical" in capsys.readouterr().out.lower()


def test_fail_on_removed(capsys) -> None:
    assert main(["diff", OLD, NEW, "--fail-on-removed"]) == 1
    capsys.readouterr()


def test_fail_on_removed_passes_when_nothing_removed(tmp_path, capsys) -> None:
    old = tmp_path / "a.md"
    new = tmp_path / "b.md"
    old.write_text("## Keep\n\nSame body text.\n", encoding="utf-8")
    new.write_text("## Keep\n\nSame body text.\n\n## More\n\nNew section here.\n", encoding="utf-8")
    assert main(["diff", str(old), str(new), "--fail-on-removed"]) == 0
    capsys.readouterr()


def test_missing_file_exits_two(tmp_path, capsys) -> None:
    assert main(["diff", str(tmp_path / "nope.md"), NEW]) == 2
    assert "error" in capsys.readouterr().err
