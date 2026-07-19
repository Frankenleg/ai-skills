# ai-skills

Cross-agent AI agent skills (Claude Code + Codex). Most skills are
**script-driven**: each skill's deterministic core lives in a bundled Python
`scaffold.py`, tested here. Some skills are prose-only. All install into both
agents' skill directories.

This repo is the **single source of truth** for these skills: the skill files +
tests live here once; other repos *reference* this repo rather than copy the
skills into themselves.

## Skills

| Skill | What it does | Needs git? |
|-------|--------------|------------|
| [`new-project`](skills/new-project/SKILL.md) | Scaffold agent instruction files: a light canonical `AGENTS.md` + a `CLAUDE.md` that imports it. Never touches git. | no |
| [`new-git-project`](skills/new-git-project/SKILL.md) | Everything `new-project` does **plus** `git init` on `main`, minimal `.gitignore` + `.gitattributes`, and an initial commit. Never creates a remote. | yes (`git` on PATH) |
| [`github-flow`](skills/github-flow/SKILL.md) | Enforce Feature Branch Workflow / GitHub Flow: branch, commit, PR, merge, cleanup. Prose skill (no script). | yes (git/gh) |

Each script-driven skill is fully standalone: `skills/<name>/` holds `SKILL.md`
+ `scaffold.py` + `test_scaffold.py`, and skills share no code. The `SKILL.md`
tells the agent to pass the project name and one-line description it knows; the
fallback (name → current directory basename, description → literal placeholder)
lives in `scaffold.py` so it is deterministic and tested. Both scaffolds are
idempotent and never overwrite an existing `AGENTS.md`/`CLAUDE.md`.

A skill is any `skills/<name>/` containing a `SKILL.md`. A `scaffold.py` is
optional: **script-driven** skills bundle one (with tests); **prose** skills
(like `github-flow`) are `SKILL.md` plus any support files (e.g. `agents/`).

## Requirements

- **Python 3.9+** — standard library only, nothing to `pip install`.
- **git** — only for the `new-git-project` skill and its tests.
- **pytest** — only to run the test suite (`pip install pytest`).

## Install

Installs each skill's files — the **entire** `skills/<name>/` tree except
`test_*.py` and `__pycache__` — into both agents' skill directories:

- Claude Code reads `~/.claude/skills/<name>/`
- Codex reads `$CODEX_HOME/skills/<name>/` (default `~/.codex/skills/<name>/`)

> **Codex path note:** skills go under `$CODEX_HOME/skills` (default
> `~/.codex/skills`), *not* `~/.agents/skills`. `~/.agents/` is Codex's
> **plugin** location (`~/.agents/plugins/marketplace.json`) — a different
> concept — so skills placed there are not discovered.

### Option A — one command (recommended)

From a clone of this repo:

    python scripts/install.py

That copies every skill under `skills/` into both directories, creating them if
needed and overwriting each skill's files in place (idempotent — safe to
re-run to update). It uses only the Python standard library.

Install just one (or a few) by naming them; an unknown name errors and installs
nothing:

    python scripts/install.py new-git-project
    python scripts/install.py new-project new-git-project

Override any path (useful for automation, testing, or a non-default home):

    python scripts/install.py \
        --skills-root ./skills \
        --claude-dir "$HOME/.claude/skills" \
        --codex-dir "$HOME/.codex/skills"

To preview without touching the real agent dirs, point `--claude-dir` /
`--codex-dir` at scratch directories and diff the result.

### Option B — manual copy (for plan→apply / provisioning repos)

If a provisioning repo prefers to diff and copy the files itself rather than
shell out to Python, replicate exactly what `install.py` does — for **each**
`skills/<name>/`:

1. Copy the entire `skills/<name>/` tree → `~/.claude/skills/<name>/…`
2. Copy the same tree                    → `~/.codex/skills/<name>/…`
3. **Skip** any `test_*.py` file and any `__pycache__/` directory — tests and
   caches stay in this repo, never installed.

### What gets installed (source → destination)

| Source (in this repo)                        | Claude Code dest                            | Codex dest (`$CODEX_HOME` or `~/.codex`) |
|-----------------------------------------------|----------------------------------------------|------------------------------------------|
| `skills/<name>/**` (except `test_*.py`, `__pycache__`) | `~/.claude/skills/<name>/…`         | `~/.codex/skills/<name>/…`               |
| `skills/<name>/test_*.py`, `__pycache__/`      | *not installed*                              | *not installed*                          |

### Check what's installed

`python scripts/install.py --check [names…]` reports each skill as
`missing` / `current` / `stale` (byte comparison) and exits non-zero if any
drift — copies nothing. Install writes a receipt `.ai-skills-install.json`
in each skills dir recording the source git commit and a per-skill SHA-256,
so you can see exactly which revision of each skill a machine has.

### Consuming from another repo

Other repos reference this one rather than vendoring the skills:

- A **private provisioning repo** can clone this repo at a pinned commit and
  run `scripts/install.py` (or `--check` first) in its plan→apply flow.
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

It discovers `skills/*/test_scaffold.py`, `skills/*/test_skill.py`, and
`scripts/test_install.py` (32 tests). Each test runs a scaffolder or the
installer in an isolated `tmp_path` and cleans up. pytest is configured for
`--import-mode=importlib` in `pyproject.toml` so identically-named test files
across skill folders don't collide.

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
│   ├── new-project/          # SKILL.md + scaffold.py + test_scaffold.py
│   ├── new-git-project/      # SKILL.md + scaffold.py + test_scaffold.py
│   └── github-flow/          # SKILL.md + agents/ + test_skill.py (prose skill)
├── scripts/
│   ├── install.py            # copy each skill dir (excl. tests/caches) → both agent dirs; --check reports drift
│   └── test_install.py
├── .githooks/pre-commit           # gitleaks secret scan
└── docs/superpowers/              # design spec + implementation plan
```

## Design

- Full design spec: [`docs/superpowers/specs/2026-07-19-ai-skills-design.md`](docs/superpowers/specs/2026-07-19-ai-skills-design.md)
- Implementation plan: [`docs/superpowers/plans/2026-07-19-script-driven-skills.md`](docs/superpowers/plans/2026-07-19-script-driven-skills.md)
