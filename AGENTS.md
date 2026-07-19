# ai-skills

Cross-agent AI agent skills (Claude Code + Codex) — script-driven skills with
tests. The canonical home for reusable skills: each skill's deterministic core
lives in a bundled Python script, tested here, and installs into both agents'
skill directories.

## Public repository — keep it clean

**This repo is public.** Never commit proprietary, personal, or sensitive
information: no secrets/keys/tokens/`.env`, no real usernames/emails/internal
hostnames/IPs, no employer/client content. Use placeholders (`<you>`,
`~/.claude/…`) in examples. When in doubt, leave it out — and remember git
history is public too. A **gitleaks pre-commit hook** in `.githooks/` blocks
commits containing secrets; enable it once per clone with
`git config core.hooksPath .githooks` (needs
[gitleaks](https://github.com/gitleaks/gitleaks) installed).

## Stack & layout

- **Python** (skill scaffolders) + **pytest** (tests).
- `skills/<name>/` — a standalone skill: `SKILL.md` + `scaffold.py` +
  `test_scaffold.py`. Each skill is independent (no shared source, no drift guard).
- `scripts/install.py` — copy each skill's runtime files (`SKILL.md` +
  `scaffold.py`) into `~/.claude/skills/` and `~/.codex/skills/`
  (`$CODEX_HOME/skills` when set).

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

- Claude Code reads `~/.claude/skills/`; Codex reads `$CODEX_HOME/skills`
  (default `~/.codex/skills/`) — the same skill installs to **both**. Codex
  skills do **not** live in `~/.agents/skills/` — that's the Codex *plugin*
  path (`~/.agents/plugins/marketplace.json`), a different concept.

> Design spec: `docs/superpowers/specs/2026-07-19-ai-skills-design.md`.
> Implementation plan: `docs/superpowers/plans/2026-07-19-script-driven-skills.md`.
> Both skills, their tests, and `scripts/install.py` are built and green. See
> `README.md` for install/consumption details.
