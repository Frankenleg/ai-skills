import hashlib
import importlib.util
import subprocess
from pathlib import Path

_spec = importlib.util.spec_from_file_location(
    "new_git_project_scaffold", Path(__file__).parent / "scaffold.py"
)
sc = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(sc)

CLAUDE_CANONICAL = (
    "@AGENTS.md\n\n"
    "<!-- AGENTS.md is the canonical instruction file. Codex reads AGENTS.md\n"
    "     natively; Claude Code reads CLAUDE.md, so this file imports it. Add\n"
    "     Claude-only instructions below the import if ever needed. -->\n"
)

SCAFFOLD_FILES = [".gitattributes", ".gitignore", "AGENTS.md", "CLAUDE.md"]


def _git(target, *args):
    return subprocess.run(
        ["git", "-C", str(target), *args],
        capture_output=True, text=True, check=True,
    ).stdout.strip()


def _tracked(target):
    out = _git(target, "ls-tree", "-r", "--name-only", "HEAD")
    return sorted(out.splitlines()) if out else []


def test_A_supplied_metadata(tmp_path):
    sc.scaffold(tmp_path, "MyProj", "A cool tool.")
    agents = (tmp_path / "AGENTS.md").read_text(encoding="utf-8")
    assert agents.splitlines()[0] == "# MyProj"
    assert "A cool tool." in agents
    assert sc.DEFAULT_DESCRIPTION not in agents
    assert (tmp_path / "CLAUDE.md").read_text(encoding="utf-8") == CLAUDE_CANONICAL
    assert (tmp_path / ".git").is_dir()
    assert (tmp_path / ".gitignore").exists()
    assert (tmp_path / ".gitattributes").exists()
    assert _git(tmp_path, "rev-parse", "--abbrev-ref", "HEAD") == "main"
    assert _tracked(tmp_path) == SCAFFOLD_FILES
    assert _git(tmp_path, "status", "--porcelain") == ""
    assert _git(tmp_path, "remote") == ""
    assert _git(tmp_path, "log", "-1", "--pretty=%s") == "Initial project scaffold"


def test_B_preserves_existing_instruction_files(tmp_path):
    (tmp_path / "AGENTS.md").write_text("ORIGINAL AGENTS\n", encoding="utf-8")
    (tmp_path / "CLAUDE.md").write_text("ORIGINAL CLAUDE\n", encoding="utf-8")
    a_before = hashlib.sha256((tmp_path / "AGENTS.md").read_bytes()).hexdigest()
    c_before = hashlib.sha256((tmp_path / "CLAUDE.md").read_bytes()).hexdigest()
    sc.scaffold(tmp_path, "X", "y")
    assert hashlib.sha256((tmp_path / "AGENTS.md").read_bytes()).hexdigest() == a_before
    assert hashlib.sha256((tmp_path / "CLAUDE.md").read_bytes()).hexdigest() == c_before
    assert (tmp_path / ".git").is_dir()
    assert _git(tmp_path, "log", "-1", "--pretty=%s") == "Initial project scaffold"


def test_C_auto_mode_dir_name_and_placeholder(tmp_path):
    d = tmp_path / "test"
    d.mkdir()
    sc.main(["--target", str(d)])
    agents = (d / "AGENTS.md").read_text(encoding="utf-8")
    assert agents.splitlines()[0] == "# test"  # not "Test"
    assert sc.DEFAULT_DESCRIPTION in agents
    assert _tracked(d) == SCAFFOLD_FILES


def test_D_includes_preexisting_nonignored_excludes_ignored(tmp_path):
    (tmp_path / "README.md").write_text("# readme\n", encoding="utf-8")
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "existing.txt").write_text("hi\n", encoding="utf-8")
    (tmp_path / ".env").write_text("SECRET=1\n", encoding="utf-8")
    sc.scaffold(tmp_path, "X", "y")
    assert _tracked(tmp_path) == SCAFFOLD_FILES + ["README.md", "src/existing.txt"]
    assert _git(tmp_path, "status", "--porcelain") == ""


def test_idempotent_second_run_no_new_commit(tmp_path):
    sc.scaffold(tmp_path, "X", "y")
    head1 = _git(tmp_path, "rev-parse", "HEAD")
    report2 = sc.scaffold(tmp_path, "X", "y")
    head2 = _git(tmp_path, "rev-parse", "HEAD")
    assert head1 == head2
    assert report2["commit"] is None
    assert report2["git_init"] is False
    assert _git(tmp_path, "status", "--porcelain") == ""
    assert _git(tmp_path, "remote") == ""
