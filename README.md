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
