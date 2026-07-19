#!/usr/bin/env python3
"""Install each skill's runtime files into the Claude Code and Codex skill dirs.

For every skills/<name>/ that has a SKILL.md, copy the whole skill directory
(excluding test_*.py, __pycache__/, and *.pyc) into the agents'
skill-discovery directories:
  - Claude Code: ~/.claude/skills/<name>/
  - Codex:       $CODEX_HOME/skills/<name>/  (default ~/.codex/skills/<name>/)
Idempotent: overwrites the runtime files in place.

Note: Codex discovers skills under $CODEX_HOME/skills (per its bundled
skill-creator/skill-installer), NOT under ~/.agents/skills — that path is for
Codex *plugins* (~/.agents/plugins/marketplace.json), a different concept.
"""
from __future__ import annotations

import argparse
import os
import shutil
import sys
from pathlib import Path


def _is_excluded(rel) -> bool:
    """test_*.py, __pycache__/, and *.pyc are never installed."""
    parts = rel.parts
    if any(p == "__pycache__" for p in parts):
        return True
    if rel.suffix == ".pyc":
        return True
    if rel.name.startswith("test_") and rel.suffix == ".py":
        return True
    return False


def runtime_files(skill_dir):
    """Sorted relative paths of a skill's installable files (excludes tests/caches)."""
    skill_dir = Path(skill_dir)
    rels = [
        p.relative_to(skill_dir)
        for p in skill_dir.rglob("*")
        if p.is_file() and not _is_excluded(p.relative_to(skill_dir))
    ]
    return sorted(rels)


def default_claude_dir() -> Path:
    """Claude Code's skill-discovery directory."""
    return Path.home() / ".claude" / "skills"


def default_codex_dir() -> Path:
    """Codex's skill-discovery directory: $CODEX_HOME/skills, else ~/.codex/skills."""
    codex_home = os.environ.get("CODEX_HOME")
    base = Path(codex_home) if codex_home else Path.home() / ".codex"
    return base / "skills"


def discover_skills(skills_root):
    skills_root = Path(skills_root)
    return sorted(
        p for p in skills_root.iterdir()
        if p.is_dir() and (p / "SKILL.md").exists()
    )


def install(skills_root, dests, names=None) -> dict:
    skills = discover_skills(skills_root)
    if names:
        by_name = {p.name: p for p in skills}
        unknown = [n for n in names if n not in by_name]
        if unknown:
            available = ", ".join(sorted(by_name)) or "(none)"
            raise ValueError(
                f"unknown skill(s): {', '.join(unknown)}; available: {available}"
            )
        skills = [by_name[n] for n in names]
    report = {"copied": []}
    for skill in skills:
        for dest_root in dests:
            dest = Path(dest_root) / skill.name
            for rel in runtime_files(skill):
                target = dest / rel
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(skill / rel, target)
                report["copied"].append(str(target))
    return report


def main(argv=None) -> int:
    repo_root = Path(__file__).resolve().parent.parent
    parser = argparse.ArgumentParser(
        description="Install skills into the Claude Code and Codex skill dirs."
    )
    parser.add_argument("names", nargs="*",
                        help="Skill name(s) to install (default: all).")
    parser.add_argument("--skills-root", default=str(repo_root / "skills"))
    parser.add_argument("--claude-dir", default=str(default_claude_dir()),
                        help="Claude Code skills dir (default: ~/.claude/skills).")
    parser.add_argument("--codex-dir", default=str(default_codex_dir()),
                        help="Codex skills dir (default: $CODEX_HOME/skills "
                             "or ~/.codex/skills).")
    args = parser.parse_args(argv)

    dests = [Path(args.claude_dir), Path(args.codex_dir)]
    try:
        report = install(Path(args.skills_root), dests, args.names or None)
    except ValueError as e:
        print(f"error: {e}", file=sys.stderr)
        return 2
    for f in report["copied"]:
        print(f"installed {f}")
    print(f"done: {len(report['copied'])} files across {len(dests)} agent dirs")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
