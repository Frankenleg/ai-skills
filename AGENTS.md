# ai-skills

Cross-agent AI agent skills (Claude Code + Codex) — script-driven skills with
tests. The canonical home for reusable skills: each skill's deterministic core
lives in a bundled script, tested here, and installs into both agents' skill
directories.

## Stack & layout

- `skills/<name>/SKILL.md` — the skill (open Agent Skills format) + bundled
  script(s) for its deterministic core.
- `<test framework — TBD>` — tests exercise the skill scripts directly.
- `<install script — TBD>` — copy skills into `~/.claude/skills/` and
  `~/.agents/skills/`.

## Build / test / run

- Test: `<TBD — test runner for the skill scripts>`
- Install locally: `<TBD — copy skills/* into both agent skill dirs>`

## Conventions

- Skills follow the open Agent Skills standard (`name` + `description` + body).
- Deterministic steps live in **bundled scripts** (script-driven skills), not
  prose — so behavior is repeatable and testable.

## Gotchas

- Claude Code reads `~/.claude/skills/`; Codex reads `~/.agents/skills/` — the
  same skill installs to **both**.

> Design in progress — the spec lives in `docs/superpowers/specs/`. Stack,
> test framework, and install mechanism will be filled in once the design is
> approved.
