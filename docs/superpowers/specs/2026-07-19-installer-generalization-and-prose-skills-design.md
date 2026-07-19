# Installer generalization + prose skills + versioning — Design Spec

**Date:** 2026-07-19
**Status:** Approved design; implementation pending (next: writing-plans).

Builds on the original [`ai-skills` design](2026-07-19-ai-skills-design.md). That
spec established script-driven skills (`SKILL.md` + `scaffold.py` + tests) and a
`scripts/install.py` that copies two named runtime files into the agent skill
dirs. This spec extends the repo in four ways so it can host a wider class of
skills and be consumed reproducibly.

## Purpose

1. **Host prose (non-script) skills**, not just script-driven ones — starting
   with `github-flow` (a git-workflow enforcement skill: `SKILL.md` + a Codex
   `agents/openai.yaml`, no `scaffold.py`).
2. **Generalize the installer** to copy a skill's *entire* directory (minus
   tests), so skills with subdirectories/extra files install correctly.
3. **Add a `--check` (dry-run) mode** so a consumer can see what is
   missing/stale before installing.
4. **Add lightweight versioning** so any machine can record and verify — **per
   skill** — which revision it has, via the source commit SHA plus a per-skill
   content hash (no hand-maintained version number).

A consumer of this repo (e.g. a downstream provisioning tool) can then clone at
a pinned commit, run `install.py --check` to plan, and `install.py` to apply —
with the copy logic living here, once.

## Decisions

- **Prose skills are first-class.** A skill is any `skills/<name>/` containing a
  `SKILL.md`. A `scaffold.py` is optional (script-driven skills have one; prose
  skills do not). This broadens the repo's scope from "script-driven only."
- **`github-flow` moves in** as the first prose skill, version-controlled here
  rather than living only inside a downstream consumer.
- **Installer copies the whole skill tree**, excluding test files and Python
  caches — not a hardcoded runtime-file list. This is required because
  `github-flow` ships `agents/openai.yaml` in a subdirectory, which the current
  two-file installer silently drops.
- **`--check` is byte-comparison drift detection**, not just presence: a skill
  whose installed files differ from the repo's is `stale`, not `current`.
- **No hand-maintained version number.** Reproducibility is the git commit SHA
  (a consumer pins it); per-skill identity is a content hash recorded in an
  install receipt. This is granular by construction — an unchanged skill's
  recorded hash never moves when a sibling changes — and needs no manual bumping.
- **Privacy:** this repo is public. It must not name any private consumer repo.
  Existing references to a specific private provisioning repo (in `README.md`
  and the prior spec/plan) are scrubbed to generic wording as part of this work.

## Scope

### 1. `github-flow` prose skill

New `skills/github-flow/`:
- `SKILL.md` — the git-workflow enforcement skill (frontmatter `name:
  github-flow` + `description`, then the prose workflow). Moved verbatim from the
  consumer that currently vendors it.
- `agents/openai.yaml` — Codex display metadata (`display_name`,
  `short_description`, `default_prompt`).
- `test_skill.py` — a **structure test** (prose skills have no `scaffold.py` to
  unit-test, so the test validates the skill's shape instead):
  - `SKILL.md` exists and has YAML frontmatter with a non-empty `name` and
    `description`;
  - `name` frontmatter equals the directory name (`github-flow`);
  - the skill directory contains no `test_*.py` beyond this one being excluded
    from install (asserted via the installer, see §2 tests).

`github-flow` has **no `scaffold.py`** — it is prose-only by design (a process
skill has no deterministic file-writing core to script).

### 2. Generalized installer (`scripts/install.py`)

Replace the fixed `RUNTIME_FILES = ("SKILL.md", "scaffold.py")` copy with a
**recursive tree copy** of `skills/<name>/`, excluding:
- any file matching `test_*.py`,
- `__pycache__/` directories and `*.pyc`,
- (defensively) any `.pytest_cache` / dotfile caches.

Behavior otherwise unchanged: discover skills by `SKILL.md` presence; install to
both agent dirs; idempotent overwrite of runtime files in place; named-subset
install with unknown-name error; overridable paths. Result: `github-flow`
installs with its `agents/openai.yaml`; script-driven skills install `SKILL.md`
+ `scaffold.py` exactly as before; `test_*.py` never installed.

### 3. `--check` (dry-run) mode

`install.py --check [names...]` copies nothing. For each in-scope skill, compare
every would-be-installed source file against the corresponding installed file in
**each** agent dir and classify the skill:

- `missing` — the skill dir (or a runtime file) is absent in an agent dir;
- `stale` — present but at least one installed file differs (byte compare) from
  the repo source;
- `current` — all runtime files present and byte-identical.

Print one line per skill per agent dir (or a compact per-skill summary), and
**exit non-zero if any skill is `missing` or `stale`** in any agent dir (so a
consumer can gate on the exit code); exit `0` when everything is `current`.
`--check` respects the same `--claude-dir` / `--agents-dir` / `--skills-root`
overrides as install.

### 4. Versioning (commit SHA + per-skill content hash)

No hand-maintained version number and **no repo-level `VERSION` file**.
Reproducibility comes from the **git commit SHA** (a consumer pins it); per-skill
identity/drift comes from content. On install (not `--check`), write a
**receipt** to each agent skills dir, `.ai-skills-install.json`:

```json
{
  "commit": "<source commit SHA, or null if source isn't a git checkout>",
  "installedAt": "<ISO 8601, or null>",
  "skills": {
    "<name>": { "hash": "<sha256 over this skill's installed runtime files>" }
  }
}
```

- `commit` — `git -C <repo> rev-parse HEAD` when the source is a git checkout,
  else `null`.
- per-skill `hash` — SHA-256 over that skill's installed runtime files (sorted
  relative path + bytes). Recorded **independently per skill**, so an unchanged
  skill's hash never moves when a sibling changes.
- `installedAt` — system clock at install time.

`--check` reads the receipt (if present) and reports, per skill, the recorded
hash vs. the repo's current hash alongside the missing/current/stale status —
"what do I have vs. what's here", per skill. There is no aggregate version to
over-bump. The load-bearing drift signal remains §3's byte compare; the receipt
is the durable per-skill record.

### 5. Docs + privacy scrub

- `README.md`: document prose skills (a skill needs a `SKILL.md`; `scaffold.py`
  is optional), the whole-dir install, `--check`, and versioning. Add
  `github-flow` to the skills table.
- **Scrub every reference to any specific private consumer repo** from
  `README.md`, [`2026-07-19-ai-skills-design.md`](2026-07-19-ai-skills-design.md),
  and [`2026-07-19-script-driven-skills.md`](../plans/2026-07-19-script-driven-skills.md),
  replacing the named private repo with generic wording ("a private provisioning
  repo", "a downstream consumer"). This repo is public and must not disclose the
  private repo's name.

## Repository layout (after)

```
ai-skills/
├── README.md                        # updated: prose skills, --check, versioning; no private-repo name
├── skills/
│   ├── new-project/                 # unchanged (script-driven)
│   ├── new-git-project/             # unchanged (script-driven)
│   └── github-flow/                 # NEW (prose)
│       ├── SKILL.md
│       ├── agents/openai.yaml
│       └── test_skill.py            # structure test (not installed)
├── scripts/
│   ├── install.py                   # generalized: whole-dir copy, --check, receipt
│   └── test_install.py              # extended tests
└── docs/superpowers/…               # scrubbed of private-repo name
```

## Tests (pytest)

- **`github-flow` structure** (`skills/github-flow/test_skill.py`): SKILL.md +
  frontmatter present; `name` == `github-flow`; description non-empty.
- **Installer whole-dir copy** (`scripts/test_install.py`): installing
  `github-flow` into scratch agent dirs copies `SKILL.md` **and**
  `agents/openai.yaml`, and does **not** copy any `test_*.py`. Script-driven
  skills still install `SKILL.md` + `scaffold.py`.
- **`--check` states:** against scratch dirs — `missing` before install
  (non-zero exit); `current` immediately after install (zero exit); `stale`
  after mutating one installed file (non-zero exit).
- **Receipt:** install writes `.ai-skills-install.json` recording the source
  `commit` (when the source is a git checkout) and a per-skill content `hash`
  for each installed skill. Changing one skill's files changes only that skill's
  recorded hash, not its siblings'. `--check` surfaces the recorded per-skill
  hash vs. the current one.
- Existing `new-project` / `new-git-project` scaffold tests remain green.

## Out of scope

- CI workflow (deferred, as in the original spec).
- Any change to how a downstream consumer is wired — that lives in the
  consumer's own repo/spec.
- Converting `github-flow` into a script-driven skill (it is prose by design).
