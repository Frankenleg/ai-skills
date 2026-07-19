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
import hashlib
import json
import os
import shutil
import subprocess
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


def _select_skills(skills_root, names):
    skills = discover_skills(skills_root)
    if not names:
        return skills
    by_name = {p.name: p for p in skills}
    unknown = [n for n in names if n not in by_name]
    if unknown:
        available = ", ".join(sorted(by_name)) or "(none)"
        raise ValueError(
            f"unknown skill(s): {', '.join(unknown)}; available: {available}"
        )
    return [by_name[n] for n in names]


RECEIPT_NAME = ".ai-skills-install.json"


def skill_hash(skill_dir) -> str:
    outer = hashlib.sha256()
    for rel in runtime_files(skill_dir):
        file_digest = hashlib.sha256(
            (Path(skill_dir) / rel).read_bytes()
        ).hexdigest()  # fixed 64-char hex, contains no NUL
        outer.update(rel.as_posix().encode("utf-8"))
        outer.update(b"\0")
        outer.update(file_digest.encode("ascii"))
        outer.update(b"\0")
    return outer.hexdigest()


def source_commit(repo_root):
    try:
        out = subprocess.run(
            ["git", "-C", str(repo_root), "rev-parse", "HEAD"],
            capture_output=True, text=True, check=True,
        )
        return out.stdout.strip() or None
    except (subprocess.CalledProcessError, FileNotFoundError, OSError):
        return None


def _read_receipt(dest_root):
    path = Path(dest_root) / RECEIPT_NAME
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (ValueError, OSError):
        return {}


def _write_receipt(dest_root, skills, commit, installed_at):
    existing = _read_receipt(dest_root)
    merged_skills = dict(existing.get("skills", {}))
    for skill in skills:
        merged_skills[skill.name] = {"hash": skill_hash(skill)}
    data = {
        "commit": commit,
        "installedAt": installed_at,
        "skills": merged_skills,
    }
    Path(dest_root).mkdir(parents=True, exist_ok=True)
    (Path(dest_root) / RECEIPT_NAME).write_text(
        json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )


def install(skills_root, dests, names=None, commit=None, installed_at=None,
            write_receipt=True) -> dict:
    skills = _select_skills(skills_root, names)
    report = {"copied": []}
    for skill in skills:
        for dest_root in dests:
            dest = Path(dest_root) / skill.name
            for rel in runtime_files(skill):
                target = dest / rel
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(skill / rel, target)
                report["copied"].append(str(target))
    if write_receipt:
        for dest_root in dests:
            _write_receipt(dest_root, skills, commit, installed_at)
    return report


def _classify(skill_dir, installed_dir) -> str:
    installed_dir = Path(installed_dir)
    if not installed_dir.exists():
        return "missing"
    any_stale = False
    for rel in runtime_files(skill_dir):
        inst_file = installed_dir / rel
        if not inst_file.exists():
            return "missing"          # missing takes precedence over stale
        if (Path(skill_dir) / rel).read_bytes() != inst_file.read_bytes():
            any_stale = True          # keep scanning: a later file may be missing
    return "stale" if any_stale else "current"


def check(skills_root, dests, names=None) -> dict:
    skills = _select_skills(skills_root, names)
    report = {"skills": {}, "drift": False}
    for skill in skills:
        per_dest = {}
        for dest_root in dests:
            status = _classify(skill, Path(dest_root) / skill.name)
            recorded = _read_receipt(dest_root).get("skills", {}).get(
                skill.name, {}).get("hash")
            per_dest[str(dest_root)] = {
                "status": status,
                "recordedHash": recorded,
                "currentHash": skill_hash(skill),
            }
            if status != "current":
                report["drift"] = True
        report["skills"][skill.name] = per_dest
    return report


def main(argv=None) -> int:
    repo_root = Path(__file__).resolve().parent.parent
    from datetime import datetime, timezone
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
    parser.add_argument("--check", action="store_true",
                        help="Report install status (missing/current/stale); copy nothing.")
    args = parser.parse_args(argv)

    dests = [Path(args.claude_dir), Path(args.codex_dir)]
    if args.check:
        try:
            report = check(Path(args.skills_root), dests, args.names or None)
        except ValueError as e:
            print(f"error: {e}", file=sys.stderr)
            return 2
        for name, per_dest in sorted(report["skills"].items()):
            statuses = ", ".join(
                f"{Path(d).name}:{v['status']}" for d, v in per_dest.items()
            )
            print(f"{name}: {statuses}")
        if report["drift"]:
            print("drift: some skills are missing or stale", file=sys.stderr)
            return 1
        print("all skills current")
        return 0
    try:
        report = install(Path(args.skills_root), dests, args.names or None,
                         commit=source_commit(repo_root),
                         installed_at=datetime.now(timezone.utc).isoformat())
    except ValueError as e:
        print(f"error: {e}", file=sys.stderr)
        return 2
    for f in report["copied"]:
        print(f"installed {f}")
    print(f"done: {len(report['copied'])} files across {len(dests)} agent dirs")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
