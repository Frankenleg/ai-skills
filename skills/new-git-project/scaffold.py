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

DECISIONS_PATH = "docs/decisions.md"

DECISIONS_TEMPLATE = """\
# Decision records

Non-obvious decisions for this project, recorded here (not only in an agent's
memory) so any coding agent shares one source of truth. Append a new dated entry
at the bottom; never rewrite history. When a decision has a testable surface,
lock it with a test and cite it under **Locked by**.

Format per entry: **Decision** / **Reason** / **Alternatives rejected** /
**Locked by**.

<!-- Append entries below, newest last:

## YYYY-MM-DD — <short title>
**Decision:** ...
**Reason:** ...
**Alternatives rejected:** ...
**Locked by:** <test path, or "convention only">
-->
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

    # 2-3. create the scaffold files, only if missing
    for fname, content in (
        (".gitignore", GITIGNORE_CONTENT),
        (".gitattributes", GITATTRIBUTES_CONTENT),
        ("AGENTS.md", render_agents(name, description)),
        ("CLAUDE.md", CLAUDE_CONTENT),
        (DECISIONS_PATH, DECISIONS_TEMPLATE),
    ):
        p = target / fname
        if p.exists():
            report["found"].append(fname)
        else:
            p.parent.mkdir(parents=True, exist_ok=True)
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
