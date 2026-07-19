# ai-skills — Design Spec

**Date:** 2026-07-19
**Status:** Approved design; implementation pending (next: writing-plans).

## Purpose

A dedicated, public home for reusable **cross-agent AI skills** (Claude Code +
Codex), each implemented as a **script-driven skill** with its own tests. Solves
the single-source-of-truth problem: the skill files + tests live here once;
other repos *reference* rather than *copy*.

- `ai-maintenance` (public docs) **links** to this repo — no skill files.
- `windows-setup` (private provisioning) **installs** from it via clone + copy in
  its plan→apply flow.

## Decisions

- **Dedicated public repo** `ai-skills` (created, scaffolded via `new-git-project`).
- **Script-driven skills:** the deterministic core lives in a bundled Python
  script the `SKILL.md` tells the agent to run; only judgment (name/description)
  stays in prose. Applies the repo owner's own "script-driven skills" principle.
- **Two fully standalone skills** — `new-project` and `new-git-project` — each
  with its **own** `scaffold.py`, free to diverge. No shared source, no drift
  guard, no `--git` coupling (`new-git-project/scaffold.py` simply does more).
- **Language:** Python + **pytest**. Portable across Windows/Linux/macOS.
- **Tests live inside each skill folder** (code + tests together); not installed.
- **Consumption:** clone + copy (fits windows-setup plan→apply). A `scripts/install.py`
  gives anyone a one-command install.
- **CI: deferred** (may add a GitHub Actions pytest workflow later).

## Repository layout

```
ai-skills/
├── AGENTS.md / CLAUDE.md
├── README.md                       # what it is; install & usage
├── skills/
│   ├── new-project/
│   │   ├── SKILL.md                # prose → run scaffold.py; agent supplies name/desc
│   │   ├── scaffold.py             # writes AGENTS.md + CLAUDE.md (no git)
│   │   └── test_scaffold.py        # pytest; repo-only (not installed)
│   └── new-git-project/
│       ├── SKILL.md
│       ├── scaffold.py             # git init + .gitignore + .gitattributes + files + commit
│       └── test_scaffold.py
├── scripts/install.py              # copy each skill's SKILL.md + scaffold.py → both agent dirs
├── tests/ (optional shared helpers)
├── pyproject.toml                  # pytest config
└── docs/superpowers/specs/         # this spec
```

## Skill model (script-driven)

Each `SKILL.md` is short: the **agent** supplies the project name and one-line
description when it has them (the judgment part), then runs the skill's
`scaffold.py`. Because the agent builds the command line, this **sidesteps
Codex's lack of argument placeholders** — the script receives clean inputs on
either agent.

Crucially, the **fallback lives in `scaffold.py`, not the prose**: if `--name`
is omitted the script defaults it to the current directory's basename; if
`--description` is omitted it uses the literal placeholder
`<one-line description — fill in>`. This keeps auto-mode behavior deterministic
and **testable** (Test C). The `SKILL.md` just tells the agent to pass what it
knows and report any defaults that kicked in.

`scaffold.py` contracts (per skill, standalone):

### `new-project/scaffold.py`
- Args: `--name` (default: current dir basename), `--description` (default: the
  literal placeholder). Agent passes them when known.
- Behavior: create `AGENTS.md` (light skeleton with the given name/description)
  and `CLAUDE.md` (`@AGENTS.md` + comment). **Never** touches git. Does not
  overwrite existing `AGENTS.md`/`CLAUDE.md` (reports and skips).
- Output: report of files created vs. skipped.

### `new-git-project/scaffold.py`
- Args: `--name` (default: current dir basename), `--description` (default: the
  literal placeholder). Agent passes them when known.
- Behavior (additive & idempotent):
  1. `git init` on `main` if not already a repo.
  2. Create `.gitignore` if absent; `.gitattributes` if absent.
  3. Create `AGENTS.md` / `CLAUDE.md` **only if missing** (preserve existing byte-for-byte).
  4. If the repo has **no commits**, `git add --all` and commit `Initial project scaffold`.
     If it already has history, make no commit.
  5. Never create a remote.
- Output: report of git init / files created vs. found / commit made.

## Tests

`pytest`, discovering `skills/*/test_scaffold.py`. Each test runs the skill's
`scaffold.py` in an isolated `tmp_path` and cleans up automatically.

**new-git-project** (from the Codex regression spec):
- **A** — supplied metadata → `# <Name>` title exactly; description verbatim (not
  a placeholder); `CLAUDE.md` matches the canonical template exactly; `.git`,
  `.gitignore`, `.gitattributes`, commit all present; commit contains exactly the
  four scaffold files; clean worktree; no remote.
- **B** — run after files already exist → existing `AGENTS.md`/`CLAUDE.md`
  preserved (SHA-256 compare); git initialized; commit made.
- **C** — no metadata, dir named `test` → name defaults to `test` (not `Test`);
  description is the literal placeholder; rest as A.
- **D** — pre-existing `README.md` + `src/existing.txt` + ignored `.env` →
  initial commit contains the 4 scaffold files **plus** the 2 pre-existing
  non-ignored files (6 total); `.env` excluded; clean worktree.
- **Idempotency** — running again on a committed repo makes no new commit, changes
  nothing, no remote.

**new-project** (lighter): files created; description verbatim / placeholder in
auto mode; canonical `CLAUDE.md`; **no** `.git`/`.gitignore`/`.gitattributes`;
no unrelated files.

## Install & consumption

> **Correction (2026-07-19):** the Codex skills path below was originally written
> as `~/.agents/skills` — that is wrong. Codex discovers skills under
> `$CODEX_HOME/skills` (default `~/.codex/skills`), per its bundled
> skill-creator/skill-installer. `~/.agents/` is the Codex *plugin* path
> (`~/.agents/plugins/marketplace.json`), a different concept. `install.py` and
> the docs use the corrected `~/.codex/skills` path.

- **`scripts/install.py`** — for each skill, copy `SKILL.md` + `scaffold.py`
  (skip `test_*.py`) into `~/.claude/skills/<name>/` and `~/.codex/skills/<name>/`
  (`$CODEX_HOME/skills` when set). One-command install for any user.
- **windows-setup** — clone `ai-skills`; plan→apply copies the same runtime files
  into both agent dirs (may call `install.py` or diff+copy itself). Update its
  `phase2-agent-config-sync` note to point at this repo.
- **ai-maintenance** — remove `shared/skills/`; turn the scaffolding doc into a
  pointer to `ai-skills` (keeps the concept, links to the repo).
- **Live machine** — reinstall both skills from `ai-skills` so
  `~/.claude/skills` and `~/.codex/skills` get the script-driven versions.

## Migration (order)

1. Implement `ai-skills`: two skills (SKILL.md + scaffold.py + tests), `install.py`,
   `README.md`, `pyproject.toml`. Run pytest green.
2. Install to the live machine (`install.py`), replacing the current prose skills.
3. Update `ai-maintenance`: drop `shared/skills/`, repoint the scaffolding doc.
4. Update `windows-setup` (memory/plan) to consume `ai-skills`.

## Out of scope / deferred

- CI (GitHub Actions pytest) — deferred.
- Remote creation for scaffolded projects — never (deliberate separate step).
- A remote for `ai-skills` itself — the user creates it when ready (public).

## Open items

- Exact `pyproject.toml` / pytest config details (settle during implementation).
- Whether `install.py` also updates existing installs vs. only fresh (default:
  overwrite the two runtime files).
