# Script-Driven Skills Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

> **Correction (2026-07-19, post-merge):** the `install.py` snippets below target
> the Codex skills dir as `~/.agents/skills` — that was wrong. Codex discovers
> skills under `$CODEX_HOME/skills` (default `~/.codex/skills`); `~/.agents/` is
> the Codex *plugin* path, not skills. The shipped `scripts/install.py`, README,
> and AGENTS.md use the corrected `~/.codex/skills` default. See the design
> spec's "Install & consumption" correction note.

**Goal:** Build the two standalone script-driven skills (`new-project`, `new-git-project`) — each `SKILL.md` + `scaffold.py` + `test_scaffold.py` — plus `scripts/install.py`, `pyproject.toml`, and `README.md`, with `pytest` green.

**Architecture:** Each skill's deterministic core lives in a bundled `scaffold.py` (the "script-driven skill" principle). `SKILL.md` is short prose telling the agent to supply `--name`/`--description` when known and run the script; the *fallback* logic (name → dir basename, description → literal placeholder) lives in `scaffold.py` so it is testable. The two skills are fully standalone (no shared source); `new-git-project/scaffold.py` simply does more (git init + ignore/attributes + commit). Tests live inside each skill folder and run the sibling `scaffold.py` in `tmp_path`.

**Tech Stack:** Python 3.9+ (stdlib only: `argparse`, `pathlib`, `subprocess`, `shutil`), pytest, git.

## Global Constraints

- **Public repo hygiene:** no secrets/personal data in any file (see `AGENTS.md`). Use placeholders in examples.
- **Line endings:** every file `scaffold.py` writes MUST be written with `open(path, "w", encoding="utf-8", newline="\n")` (LF). This is deterministic across Windows/Linux/macOS and keeps the git worktree clean under any `core.autocrlf` setting.
- **Canonical `CLAUDE.md`** (byte-exact, LF), produced by both scaffolds:
  ```
  @AGENTS.md

  <!-- AGENTS.md is the canonical instruction file. Codex reads AGENTS.md
       natively; Claude Code reads CLAUDE.md, so this file imports it. Add
       Claude-only instructions below the import if ever needed. -->
  ```
- **Canonical `AGENTS.md` skeleton** (name/description filled, rest literal `<placeholders>`):
  ```
  # {name}

  {description}

  ## Stack & layout
  - <language/framework, key directories, entry points>

  ## Build / test / run
  - Build: <command>
  - Test: <command>
  - Run: <command>

  ## Conventions
  - <project-specific conventions only>

  ## Gotchas
  - <anything non-obvious about this project>
  ```
- **Defaults:** `--name` default = target directory basename (NOT title-cased — `test` stays `test`); `--description` default = literal `<one-line description — fill in>`.
- **pytest two-file collision:** both skills have `test_scaffold.py`; both have `scaffold.py`. Use `--import-mode=importlib` in `pyproject.toml` AND load the sibling `scaffold.py` in each test via `importlib.util.spec_from_file_location` with a **unique module name** per skill. Never `import scaffold` directly.
- **Never create a git remote.** Ever.

---

### Task 1: Project config — `pyproject.toml` + `README.md`

**Files:**
- Create: `pyproject.toml`
- Create: `README.md`

**Interfaces:**
- Produces: pytest configuration (`--import-mode=importlib`, `testpaths = ["skills", "scripts"]`) that every later task's tests rely on.

- [ ] **Step 1: Create `pyproject.toml`**

```toml
[project]
name = "ai-skills"
version = "0.0.0"
description = "Cross-agent AI skills (Claude Code + Codex) — script-driven, tested."
requires-python = ">=3.9"

[tool.pytest.ini_options]
addopts = "--import-mode=importlib"
testpaths = ["skills", "scripts"]
```

- [ ] **Step 2: Create `README.md`**

```markdown
# ai-skills

Cross-agent AI agent skills (Claude Code + Codex) — **script-driven** skills with
tests. Each skill's deterministic core lives in a bundled Python `scaffold.py`,
tested here, and installs into both agents' skill directories.

## Skills

- **`new-project`** — scaffold agent instruction files (`AGENTS.md` + `CLAUDE.md`).
  No git.
- **`new-git-project`** — scaffold as a git repo: `git init` on `main`,
  `.gitignore` + `.gitattributes`, the instruction files, and an initial commit.
  Never creates a remote.

Each skill is standalone: `skills/<name>/` holds `SKILL.md` + `scaffold.py` +
`test_scaffold.py`. The `SKILL.md` tells the agent to pass the project name and
one-line description it knows; the fallback (name → directory basename,
description → placeholder) lives in `scaffold.py` so it is deterministic and
tested.

## Test

    pytest

## Install

Copy each skill's runtime files (`SKILL.md` + `scaffold.py`, not the tests) into
the Claude Code and Codex skill directories:

    python scripts/install.py

Installs into `~/.claude/skills/<name>/` (Claude Code) and
`~/.agents/skills/<name>/` (Codex).
```

- [ ] **Step 3: Commit**

```bash
git checkout -b claude/script-driven-skills
git add pyproject.toml README.md
git commit -m "Add pyproject (pytest config) and README"
```

---

### Task 2: `new-project` skill

**Files:**
- Create: `skills/new-project/scaffold.py`
- Create: `skills/new-project/test_scaffold.py`
- Create: `skills/new-project/SKILL.md`

**Interfaces:**
- Produces: `scaffold(target: Path, name: str, description: str) -> dict` returning `{"created": [str], "skipped": [str]}`; `main(argv=None) -> int`; module constants `DEFAULT_DESCRIPTION`, `AGENTS_TEMPLATE`, `CLAUDE_CONTENT`; `render_agents(name, description) -> str`.

- [ ] **Step 1: Write the failing test** — `skills/new-project/test_scaffold.py`

```python
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
```

- [ ] **Step 2: Run to verify it fails**

Run: `pytest skills/new-project -v`
Expected: FAIL / collection error — `scaffold.py` does not exist yet.

- [ ] **Step 3: Write `skills/new-project/scaffold.py`**

```python
#!/usr/bin/env python3
"""Scaffold a new project's agent instruction files (no git).

Writes a light, canonical AGENTS.md plus a CLAUDE.md that imports it. The
deterministic core lives here (script-driven skill); SKILL.md only tells the
agent to pass the name/description it knows and report any defaults used.
"""
from __future__ import annotations

import argparse
from pathlib import Path

DEFAULT_DESCRIPTION = "<one-line description — fill in>"

AGENTS_TEMPLATE = """\
# {name}

{description}

## Stack & layout
- <language/framework, key directories, entry points>

## Build / test / run
- Build: <command>
- Test: <command>
- Run: <command>

## Conventions
- <project-specific conventions only>

## Gotchas
- <anything non-obvious about this project>
"""

CLAUDE_CONTENT = """\
@AGENTS.md

<!-- AGENTS.md is the canonical instruction file. Codex reads AGENTS.md
     natively; Claude Code reads CLAUDE.md, so this file imports it. Add
     Claude-only instructions below the import if ever needed. -->
"""


def render_agents(name: str, description: str) -> str:
    return AGENTS_TEMPLATE.format(name=name, description=description)


def _write(path: Path, content: str) -> None:
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write(content)


def scaffold(target, name: str, description: str) -> dict:
    """Create AGENTS.md and CLAUDE.md under target. Never touches git.

    Existing AGENTS.md/CLAUDE.md are preserved (reported as skipped).
    Returns {"created": [...], "skipped": [...]}.
    """
    target = Path(target)
    created = []
    skipped = []
    for fname, content in (
        ("AGENTS.md", render_agents(name, description)),
        ("CLAUDE.md", CLAUDE_CONTENT),
    ):
        p = target / fname
        if p.exists():
            skipped.append(fname)
        else:
            _write(p, content)
            created.append(fname)
    return {"created": created, "skipped": skipped}


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(
        description="Scaffold agent instruction files (no git)."
    )
    parser.add_argument("--name", default=None,
                        help="Project name (default: target directory name).")
    parser.add_argument("--description", default=None,
                        help="One-line description (default: placeholder).")
    parser.add_argument("--target", default=".",
                        help="Target directory (default: current directory).")
    args = parser.parse_args(argv)

    target = Path(args.target).resolve()
    name = args.name if args.name is not None else target.name
    description = (args.description if args.description is not None
                  else DEFAULT_DESCRIPTION)

    result = scaffold(target, name, description)

    for f in result["created"]:
        print(f"created  {f}")
    for f in result["skipped"]:
        print(f"skipped  {f} (already exists)")
    if args.name is None:
        print(f"note: name defaulted to directory basename '{name}'")
    if args.description is None:
        print("note: description left as placeholder — edit AGENTS.md")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

- [ ] **Step 4: Run to verify it passes**

Run: `pytest skills/new-project -v`
Expected: PASS (3 tests).

- [ ] **Step 5: Write `skills/new-project/SKILL.md`**

```markdown
---
name: new-project
description: Scaffold a new project's agent instruction files — a light canonical AGENTS.md plus a CLAUDE.md that imports it. Use when starting a new or empty project/repo that needs baseline agent guidance and you do NOT want a git repository created. Use new-git-project instead if you also want git initialized. Do not use to edit an existing, already-scaffolded instruction set.
---

# New Project Scaffolder (no git)

Set up a new project's agent instruction files using the "AGENTS.md canonical,
CLAUDE.md imports it" pattern, so Codex and Claude Code share one source of
truth. This is a **script-driven** skill: the deterministic file-writing lives
in `scaffold.py`; your only judgment is the project **name** and a one-line
**description**.

## Steps

1. **Decide the name and description.**
   - If the user gave them (conversation or arguments), use those.
   - If you can ask and don't know, ask before running.
   - If running autonomously, omit the flag(s) you don't know — `scaffold.py`
     defaults the name to the current directory's basename and leaves the
     description as a literal placeholder. Report any default that kicked in.

2. **Run the scaffolder** from the project root, passing what you know:

   ```bash
   python scaffold.py --name "<Project Name>" --description "<one-line description>"
   ```

   Omit `--name` and/or `--description` to accept the defaults. `--target`
   defaults to the current directory.

3. **Report** the files it created or skipped, and state any defaults used so
   the user can correct them. The script never touches git and never overwrites
   an existing `AGENTS.md`/`CLAUDE.md`.
```

- [ ] **Step 6: Commit**

```bash
git add skills/new-project
git commit -m "Add new-project script-driven skill with tests"
```

---

### Task 3: `new-git-project` skill

**Files:**
- Create: `skills/new-git-project/scaffold.py`
- Create: `skills/new-git-project/test_scaffold.py`
- Create: `skills/new-git-project/SKILL.md`

**Interfaces:**
- Produces: `scaffold(target, name, description) -> dict` returning `{"git_init": bool, "created": [str], "found": [str], "commit": str|None}`; `main(argv=None) -> int`; constants `DEFAULT_DESCRIPTION`, `GITIGNORE_CONTENT`, `GITATTRIBUTES_CONTENT`.
- Consumes: nothing from Task 2 (standalone — templates are duplicated by design).

- [ ] **Step 1: Write the failing test** — `skills/new-git-project/test_scaffold.py`

```python
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
```

- [ ] **Step 2: Run to verify it fails**

Run: `pytest skills/new-git-project -v`
Expected: FAIL / collection error — `scaffold.py` does not exist yet.

- [ ] **Step 3: Write `skills/new-git-project/scaffold.py`**

```python
#!/usr/bin/env python3
"""Scaffold a new project AS a git repository (additive & idempotent).

git init on `main`, minimal .gitignore/.gitattributes, the canonical AGENTS.md +
CLAUDE.md, and an initial commit if the repo has no history. Never creates a
remote. Safe to run on an empty dir, right after `new-project`, or again on an
already-set-up repo. Deterministic core of a script-driven skill.
"""
from __future__ import annotations

import argparse
import subprocess
from pathlib import Path

DEFAULT_DESCRIPTION = "<one-line description — fill in>"

AGENTS_TEMPLATE = """\
# {name}

{description}

## Stack & layout
- <language/framework, key directories, entry points>

## Build / test / run
- Build: <command>
- Test: <command>
- Run: <command>

## Conventions
- <project-specific conventions only>

## Gotchas
- <anything non-obvious about this project>
"""

CLAUDE_CONTENT = """\
@AGENTS.md

<!-- AGENTS.md is the canonical instruction file. Codex reads AGENTS.md
     natively; Claude Code reads CLAUDE.md, so this file imports it. Add
     Claude-only instructions below the import if ever needed. -->
"""

GITIGNORE_CONTENT = """\
# OS / editor cruft
Thumbs.db
.DS_Store
*.tmp

# Secrets — never commit
.env
.env.*
*.pem
*.key
id_rsa
"""

GITATTRIBUTES_CONTENT = """\
# Normalize line endings: store LF in the repo, check out native per-OS.
* text=auto

# Shell scripts must stay LF so they run on all platforms.
*.sh text eol=lf
"""


def render_agents(name: str, description: str) -> str:
    return AGENTS_TEMPLATE.format(name=name, description=description)


def _write(path: Path, content: str) -> None:
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write(content)


def _git(target, *args) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["git", "-C", str(target), *args],
        capture_output=True, text=True, check=True,
    )


def _is_repo(target: Path) -> bool:
    return (target / ".git").exists()


def _has_commits(target: Path) -> bool:
    r = subprocess.run(
        ["git", "-C", str(target), "rev-parse", "--verify", "HEAD"],
        capture_output=True, text=True,
    )
    return r.returncode == 0


def _has_identity(target: Path) -> bool:
    name = subprocess.run(["git", "-C", str(target), "config", "user.name"],
                          capture_output=True, text=True)
    email = subprocess.run(["git", "-C", str(target), "config", "user.email"],
                           capture_output=True, text=True)
    return bool(name.stdout.strip()) and bool(email.stdout.strip())


def scaffold(target, name: str, description: str) -> dict:
    """Idempotently set up target as a git repo with instruction files.

    Returns {"git_init": bool, "created": [...], "found": [...],
             "commit": "<subject>"|None}.
    """
    target = Path(target)
    report = {"git_init": False, "created": [], "found": [], "commit": None}

    # 1. git init on main (only if not already a repo)
    if not _is_repo(target):
        _git(target, "init")
        _git(target, "symbolic-ref", "HEAD", "refs/heads/main")
        report["git_init"] = True

    # 2-3. create the four scaffold files, only if missing
    for fname, content in (
        (".gitignore", GITIGNORE_CONTENT),
        (".gitattributes", GITATTRIBUTES_CONTENT),
        ("AGENTS.md", render_agents(name, description)),
        ("CLAUDE.md", CLAUDE_CONTENT),
    ):
        p = target / fname
        if p.exists():
            report["found"].append(fname)
        else:
            _write(p, content)
            report["created"].append(fname)

    # 4. initial commit only if the repo has no history yet
    if not _has_commits(target):
        _git(target, "add", "--all")
        ident = []
        if not _has_identity(target):
            ident = ["-c", "user.name=ai-skills scaffold",
                     "-c", "user.email=ai-skills@example.invalid"]
        subprocess.run(
            ["git", "-C", str(target), *ident, "commit", "-m",
             "Initial project scaffold"],
            capture_output=True, text=True, check=True,
        )
        report["commit"] = "Initial project scaffold"

    return report


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(
        description="Scaffold a new project as a git repository."
    )
    parser.add_argument("--name", default=None,
                        help="Project name (default: target directory name).")
    parser.add_argument("--description", default=None,
                        help="One-line description (default: placeholder).")
    parser.add_argument("--target", default=".",
                        help="Target directory (default: current directory).")
    args = parser.parse_args(argv)

    target = Path(args.target).resolve()
    name = args.name if args.name is not None else target.name
    description = (args.description if args.description is not None
                  else DEFAULT_DESCRIPTION)

    report = scaffold(target, name, description)

    if report["git_init"]:
        print("git: initialized empty repository on 'main'")
    else:
        print("git: already a repository (left as-is)")
    for f in report["created"]:
        print(f"created  {f}")
    for f in report["found"]:
        print(f"found    {f} (kept existing)")
    if report["commit"]:
        print(f"commit:  {report['commit']}")
    else:
        print("commit:  none (repo already has history)")
    if args.name is None:
        print(f"note: name defaulted to directory basename '{name}'")
    if args.description is None:
        print("note: description left as placeholder — edit AGENTS.md")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

- [ ] **Step 4: Run to verify it passes**

Run: `pytest skills/new-git-project -v`
Expected: PASS (5 tests).

- [ ] **Step 5: Write `skills/new-git-project/SKILL.md`**

```markdown
---
name: new-git-project
description: Scaffold a new project AS A GIT REPOSITORY — git init, a minimal .gitignore and .gitattributes, a light canonical AGENTS.md plus a CLAUDE.md that imports it, and an initial commit on main. Use when starting a new project/repo that should be version-controlled, or to add git to a project already scaffolded by new-project. Does NOT create a remote. Use new-project instead if you do NOT want git.
---

# New Git Project Scaffolder

Set up a new project as a git repository with agent instruction files, using the
"AGENTS.md canonical, CLAUDE.md imports it" pattern. This is a **script-driven**
skill: `scaffold.py` does all the deterministic, idempotent work (git init,
ignore/attributes, files, initial commit). Your only judgment is the project
**name** and a one-line **description**. Safe to run on an empty directory, right
after `new-project` (it just adds git), or again on an already-set-up project.

## Steps

1. **Decide the name and description.**
   - If the user gave them (conversation or arguments), use those.
   - If you can ask and don't know, ask before running.
   - If running autonomously, omit the flag(s) you don't know — `scaffold.py`
     defaults the name to the current directory's basename and leaves the
     description as a literal placeholder. Report any default that kicked in.

2. **Run the scaffolder** from the project root, passing what you know:

   ```bash
   python scaffold.py --name "<Project Name>" --description "<one-line description>"
   ```

   Omit `--name` and/or `--description` to accept the defaults. `--target`
   defaults to the current directory. The script is idempotent — it initializes
   git on `main` only if needed, creates each of `.gitignore`,
   `.gitattributes`, `AGENTS.md`, `CLAUDE.md` only if missing (existing files
   kept byte-for-byte), and makes the `Initial project scaffold` commit only if
   the repo has no history. It **never** creates a remote.

3. **Report** what it did — git initialized or already present, which files were
   created vs. kept, whether the initial commit was made, and any defaults used.
   Creating/pushing a remote is a separate, deliberate step for the user.
```

- [ ] **Step 6: Commit**

```bash
git add skills/new-git-project
git commit -m "Add new-git-project script-driven skill with tests"
```

---

### Task 4: `scripts/install.py` + test

**Files:**
- Create: `scripts/install.py`
- Create: `scripts/test_install.py`

**Interfaces:**
- Produces: `discover_skills(skills_root: Path) -> [Path]`; `install(skills_root, dests: [Path]) -> {"copied": [str]}`; `main(argv=None) -> int`. Copies only `SKILL.md` + `scaffold.py` (NOT `test_scaffold.py`).

- [ ] **Step 1: Write the failing test** — `scripts/test_install.py`

```python
import importlib.util
from pathlib import Path

_spec = importlib.util.spec_from_file_location(
    "install_mod", Path(__file__).parent / "install.py"
)
inst = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(inst)


def test_install_copies_runtime_files_not_tests(tmp_path):
    skills = tmp_path / "skills"
    (skills / "demo").mkdir(parents=True)
    (skills / "demo" / "SKILL.md").write_text("s", encoding="utf-8")
    (skills / "demo" / "scaffold.py").write_text("c", encoding="utf-8")
    (skills / "demo" / "test_scaffold.py").write_text("t", encoding="utf-8")
    claude = tmp_path / "claude"
    agents = tmp_path / "agents"
    report = inst.install(skills, [claude, agents])
    for root in (claude, agents):
        assert (root / "demo" / "SKILL.md").read_text(encoding="utf-8") == "s"
        assert (root / "demo" / "scaffold.py").read_text(encoding="utf-8") == "c"
        assert not (root / "demo" / "test_scaffold.py").exists()
    assert len(report["copied"]) == 4  # 2 files x 2 dests


def test_discover_skills_requires_skill_md(tmp_path):
    skills = tmp_path / "skills"
    (skills / "real").mkdir(parents=True)
    (skills / "real" / "SKILL.md").write_text("x", encoding="utf-8")
    (skills / "notaskill").mkdir(parents=True)  # no SKILL.md
    found = [p.name for p in inst.discover_skills(skills)]
    assert found == ["real"]
```

- [ ] **Step 2: Run to verify it fails**

Run: `pytest scripts -v`
Expected: FAIL / collection error — `install.py` does not exist yet.

- [ ] **Step 3: Write `scripts/install.py`**

```python
#!/usr/bin/env python3
"""Install each skill's runtime files into the Claude Code and Codex skill dirs.

For every skills/<name>/ that has a SKILL.md, copy SKILL.md + scaffold.py
(never test_*.py) into ~/.claude/skills/<name>/ and ~/.agents/skills/<name>/.
Idempotent: overwrites the two runtime files in place.
"""
from __future__ import annotations

import argparse
import shutil
from pathlib import Path

RUNTIME_FILES = ("SKILL.md", "scaffold.py")


def discover_skills(skills_root):
    skills_root = Path(skills_root)
    return sorted(
        p for p in skills_root.iterdir()
        if p.is_dir() and (p / "SKILL.md").exists()
    )


def install(skills_root, dests) -> dict:
    report = {"copied": []}
    for skill in discover_skills(skills_root):
        for dest_root in dests:
            dest = Path(dest_root) / skill.name
            dest.mkdir(parents=True, exist_ok=True)
            for fname in RUNTIME_FILES:
                src = skill / fname
                if src.exists():
                    shutil.copy2(src, dest / fname)
                    report["copied"].append(str(dest / fname))
    return report


def main(argv=None) -> int:
    repo_root = Path(__file__).resolve().parent.parent
    home = Path.home()
    parser = argparse.ArgumentParser(
        description="Install skills into the Claude Code and Codex skill dirs."
    )
    parser.add_argument("--skills-root", default=str(repo_root / "skills"))
    parser.add_argument("--claude-dir",
                        default=str(home / ".claude" / "skills"))
    parser.add_argument("--agents-dir",
                        default=str(home / ".agents" / "skills"))
    args = parser.parse_args(argv)

    dests = [Path(args.claude_dir), Path(args.agents_dir)]
    report = install(Path(args.skills_root), dests)
    for f in report["copied"]:
        print(f"installed {f}")
    print(f"done: {len(report['copied'])} files across {len(dests)} agent dirs")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

- [ ] **Step 4: Run to verify it passes**

Run: `pytest scripts -v`
Expected: PASS (2 tests).

- [ ] **Step 5: Run the full suite**

Run: `pytest`
Expected: PASS (10 tests total; no collection errors from duplicate `test_scaffold.py`).

- [ ] **Step 6: Commit**

```bash
git add scripts/install.py scripts/test_install.py
git commit -m "Add scripts/install.py with test"
```

---

## Self-Review

**Spec coverage:**
- Two standalone skills w/ own scaffold.py + tests — Tasks 2, 3. ✓
- `new-project` contract (files, no git, no-overwrite, defaults) — Task 2 tests. ✓
- `new-git-project` contract (init on main, ignore/attributes, only-if-missing, commit-if-no-history, no remote) — Task 3 scaffold + tests A–D + idempotency. ✓
- `scripts/install.py` (copy SKILL.md + scaffold.py, skip tests, both dirs) — Task 4. ✓
- `pyproject.toml` pytest config — Task 1. ✓
- `README.md` — Task 1. ✓
- Tests live in skill folders, not installed — Task 4 install skips `test_*.py`. ✓

**Placeholder scan:** none — every step has full code.

**Type consistency:** `scaffold(target, name, description)` signature identical across both skills; `_write`/`render_agents` helpers consistent; `install(skills_root, dests)` matches test calls; report dict keys (`created`/`skipped` for new-project; `git_init`/`created`/`found`/`commit` for new-git-project; `copied` for install) used consistently in code and tests.

**Deferred (out of scope, per spec):** CI workflow; remote creation; the migration steps (install to machine, ai-maintenance repoint, windows-setup update) happen AFTER pytest is green.
