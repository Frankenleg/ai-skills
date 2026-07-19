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
