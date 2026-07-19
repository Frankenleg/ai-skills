#!/usr/bin/env python3
"""Install each skill's runtime files into the Claude Code and Codex skill dirs.

For every skills/<name>/ that has a SKILL.md, copy SKILL.md + scaffold.py
(never test_*.py) into ~/.claude/skills/<name>/ and ~/.agents/skills/<name>/.
Idempotent: overwrites the two runtime files in place.
"""
from __future__ import annotations

import argparse
import shutil
import sys
from pathlib import Path

RUNTIME_FILES = ("SKILL.md", "scaffold.py")


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
    parser.add_argument("names", nargs="*",
                        help="Skill name(s) to install (default: all).")
    parser.add_argument("--skills-root", default=str(repo_root / "skills"))
    parser.add_argument("--claude-dir",
                        default=str(home / ".claude" / "skills"))
    parser.add_argument("--agents-dir",
                        default=str(home / ".agents" / "skills"))
    args = parser.parse_args(argv)

    dests = [Path(args.claude_dir), Path(args.agents_dir)]
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
