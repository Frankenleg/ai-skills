# ai-skills

Cross-agent AI agent skills (Claude Code + Codex) — script-driven skills with
tests. The canonical home for reusable skills: each skill's deterministic core
lives in a bundled Python script, tested here, and installs into both agents'
skill directories.

## Stack & layout

- **Python** (skill scaffolders) + **pytest** (tests).
- `skills/<name>/` — a standalone skill: `SKILL.md` + `scaffold.py` +
  `test_scaffold.py`. Each skill is independent (no shared source, no drift guard).
- `scripts/install.py` — copy each skill's runtime files (`SKILL.md` +
  `scaffold.py`) into `~/.claude/skills/` and `~/.agents/skills/`.

## Build / test / run

- Test: `pytest` (discovers `skills/*/test_scaffold.py`).
- Install locally: `python scripts/install.py`.

## Conventions

- Skills follow the open Agent Skills standard (`name` + `description` + body).
- Deterministic steps live in a **bundled Python script** (script-driven
  skills), not prose — so behavior is repeatable and testable.
- Skills are **standalone** — two skills may share behavior but never share
  code; each evolves independently.

## Gotchas

- Claude Code reads `~/.claude/skills/`; Codex reads `~/.agents/skills/` — the
  same skill installs to **both**.

> Full design: `docs/superpowers/specs/2026-07-19-ai-skills-design.md`.
> Implementation pending (next step: writing-plans → build the two skills + tests).
