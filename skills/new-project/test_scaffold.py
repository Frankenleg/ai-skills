import hashlib
import importlib.util
from pathlib import Path

_spec = importlib.util.spec_from_file_location(
    "new_project_scaffold", Path(__file__).parent / "scaffold.py"
)
sc = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(sc)

CLAUDE_CANONICAL = (
    "@AGENTS.md\n\n"
    "<!-- AGENTS.md is the canonical instruction file. Codex reads AGENTS.md\n"
    "     natively; Claude Code reads CLAUDE.md, so this file imports it. Add\n"
    "     Claude-only instructions below the import if ever needed. -->\n"
)


def test_creates_files_with_supplied_metadata(tmp_path):
    result = sc.scaffold(tmp_path, "MyProj", "A cool tool.")
    agents = (tmp_path / "AGENTS.md").read_text(encoding="utf-8")
    claude = (tmp_path / "CLAUDE.md").read_text(encoding="utf-8")
    assert agents.splitlines()[0] == "# MyProj"
    assert "A cool tool." in agents
    assert sc.DEFAULT_DESCRIPTION not in agents
    assert claude == CLAUDE_CANONICAL
    assert result["created"] == ["AGENTS.md", "CLAUDE.md"]
    assert not (tmp_path / ".git").exists()
    assert not (tmp_path / ".gitignore").exists()
    assert not (tmp_path / ".gitattributes").exists()


def test_auto_mode_uses_placeholder_and_dir_name(tmp_path):
    d = tmp_path / "test"
    d.mkdir()
    sc.main(["--target", str(d)])
    agents = (d / "AGENTS.md").read_text(encoding="utf-8")
    assert agents.splitlines()[0] == "# test"  # not "Test"
    assert sc.DEFAULT_DESCRIPTION in agents


def test_does_not_overwrite_existing(tmp_path):
    (tmp_path / "AGENTS.md").write_text("ORIGINAL", encoding="utf-8")
    before = hashlib.sha256((tmp_path / "AGENTS.md").read_bytes()).hexdigest()
    result = sc.scaffold(tmp_path, "X", "y")
    after = hashlib.sha256((tmp_path / "AGENTS.md").read_bytes()).hexdigest()
    assert before == after
    assert "AGENTS.md" in result["skipped"]
    assert (tmp_path / "CLAUDE.md").exists()
