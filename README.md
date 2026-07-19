# ai-skills

Cross-agent AI agent skills (Claude Code + Codex) — **script-driven** skills with
tests. Each skill's deterministic core lives in a bundled Python `scaffold.py`,
tested here, and installs into both agents' skill directories.

This repo is the **single source of truth** for these skills: the skill files +
tests live here once; other repos *reference* this repo rather than copy the
skills into themselves.

## Skills

| Skill | What it does | Needs git? |
|-------|--------------|------------|
| [`new-project`](skills/new-project/SKILL.md) | Scaffold agent instruction files: a light canonical `AGENTS.md` + a `CLAUDE.md` that imports it. Never touches git. | no |
| [`new-git-project`](skills/new-git-project/SKILL.md) | Everything `new-project` does **plus** `git init` on `main`, minimal `.gitignore` + `.gitattributes`, and an initial commit. Never creates a remote. | yes (`git` on PATH) |

Each skill is fully standalone: `skills/<name>/` holds `SKILL.md` + `scaffold.py`
+ `test_scaffold.py`, and the two skills share no code. The `SKILL.md` tells the
agent to pass the project name and one-line description it knows; the fallback
(name → current directory basename, description → literal placeholder) lives in
`scaffold.py` so it is deterministic and tested. Both scaffolds are idempotent
and never overwrite an existing `AGENTS.md`/`CLAUDE.md`.

## Requirements

- **Python 3.9+** — standard library only, nothing to `pip install`.
- **git** — only for the `new-git-project` skill and its tests.
- **pytest** — only to run the test suite (`pip install pytest`).

## Install

Installs each skill's **runtime files** — `SKILL.md` + `scaffold.py` (never the
`test_*.py`) — into both agents' skill directories:

- Claude Code reads `~/.claude/skills/<name>/`
- Codex reads `~/.agents/skills/<name>/`

### Option A — one command (recommended)

From a clone of this repo:

    python scripts/install.py

That copies every skill under `skills/` into both directories, creating them if
needed and overwriting the two runtime files in place (idempotent — safe to
re-run to update). It uses only the Python standard library.

Override any path (useful for automation, testing, or a non-default home):

    python scripts/install.py \
        --skills-root ./skills \
        --claude-dir "$HOME/.claude/skills" \
        --agents-dir "$HOME/.agents/skills"

To preview without touching the real agent dirs, point `--claude-dir` /
`--agents-dir` at scratch directories and diff the result.

### Option B — manual copy (for plan→apply / provisioning repos)

If a provisioning repo prefers to diff and copy the files itself rather than
shell out to Python, replicate exactly what `install.py` does — for **each**
`skills/<name>/`:

1. Copy `skills/<name>/SKILL.md`   → `~/.claude/skills/<name>/SKILL.md`
2. Copy `skills/<name>/scaffold.py` → `~/.claude/skills/<name>/scaffold.py`
3. Copy the same two files          → `~/.agents/skills/<name>/…`
4. **Do not** copy `test_scaffold.py` — tests stay in this repo, never installed.

### What gets installed (source → destination)

| Source (in this repo)            | Claude Code dest                       | Codex dest                        |
|----------------------------------|----------------------------------------|-----------------------------------|
| `skills/<name>/SKILL.md`         | `~/.claude/skills/<name>/SKILL.md`     | `~/.agents/skills/<name>/SKILL.md`     |
| `skills/<name>/scaffold.py`      | `~/.claude/skills/<name>/scaffold.py`  | `~/.agents/skills/<name>/scaffold.py`  |
| `skills/<name>/test_scaffold.py` | *not installed*                        | *not installed*                        |

### Consuming from another repo

Other repos reference this one rather than vendoring the skills:

- **windows-setup** (private provisioning) clones `ai-skills` and, in its
  plan→apply flow, runs `scripts/install.py` (Option A) or diff+copies the
  runtime files (Option B) into both agent dirs.
- **ai-maintenance** (public docs) links here instead of holding skill copies.

## Usage

Once installed, invoke a skill by name in the agent. The agent supplies what it
knows and runs the bundled script from the project root, e.g.:

    python scaffold.py --name "My Project" --description "One-line summary."

Omit `--name` and/or `--description` to accept the tested defaults;
`--target` defaults to the current directory. See each skill's `SKILL.md` for
the exact flow.

## Develop / test

Run the full suite from the repo root:

    pytest

It discovers `skills/*/test_scaffold.py` and `scripts/test_install.py` (10 tests).
Each test runs a scaffolder in an isolated `tmp_path` and cleans up. pytest is
configured for `--import-mode=importlib` in `pyproject.toml` so the two
identically-named `test_scaffold.py` files don't collide.

### Secret-scan pre-commit hook

This repo is **public**, so a [gitleaks](https://github.com/gitleaks/gitleaks)
pre-commit hook in `.githooks/` blocks commits that contain secrets. Enable it
once per clone (requires `gitleaks` on your PATH):

    git config core.hooksPath .githooks

If `gitleaks` isn't installed, the hook prints a warning and skips the scan
(it never blocks a commit just because the tool is missing).

## Layout

```
ai-skills/
├── AGENTS.md / CLAUDE.md          # this repo's own agent instructions
├── README.md
├── pyproject.toml                 # pytest config (import-mode=importlib)
├── skills/
│   ├── new-project/               # SKILL.md + scaffold.py + test_scaffold.py
│   └── new-git-project/           # SKILL.md + scaffold.py + test_scaffold.py
├── scripts/
│   ├── install.py                 # copy runtime files → both agent dirs
│   └── test_install.py
├── .githooks/pre-commit           # gitleaks secret scan
└── docs/superpowers/              # design spec + implementation plan
```

## Design

- Full design spec: [`docs/superpowers/specs/2026-07-19-ai-skills-design.md`](docs/superpowers/specs/2026-07-19-ai-skills-design.md)
- Implementation plan: [`docs/superpowers/plans/2026-07-19-script-driven-skills.md`](docs/superpowers/plans/2026-07-19-script-driven-skills.md)
