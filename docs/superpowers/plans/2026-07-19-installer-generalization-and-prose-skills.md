# Installer generalization + prose skills + versioning — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Extend `ai-skills` to host prose (non-script) skills — starting with `github-flow` — by generalizing `install.py` to whole-directory copy, adding a `--check` dry-run, a per-skill content-hash install receipt, and scrubbing any private-consumer name from the public repo.

**Architecture:** Pure Python standard library. `scripts/install.py` gains a `runtime_files()` file-selector (excludes tests/caches), a `check()` drift reporter, and a `.ai-skills-install.json` receipt recording the source git commit + a per-skill SHA-256. Skills are directories under `skills/<name>/` containing a `SKILL.md` (a `scaffold.py` is optional). Everything is tested with pytest against `tmp_path` scratch dirs.

**Tech Stack:** Python 3.9+ (stdlib only — `argparse`, `shutil`, `hashlib`, `json`, `subprocess`, `pathlib`), pytest (`--import-mode=importlib`).

## Global Constraints

- **Python 3.9+, standard library only** in runtime code — nothing to `pip install`. pytest is a dev-only dependency.
- **Tests** run from the repo root with `pytest`; pyproject sets `--import-mode=importlib` and `testpaths = ["skills", "scripts"]`. Load `install.py` in tests via `importlib.util.spec_from_file_location` (see the existing `scripts/test_install.py`). Each test uses an isolated `tmp_path`.
- **A skill is any `skills/<name>/` containing a `SKILL.md`.** `scaffold.py` is optional (script-driven skills have one; prose skills do not).
- **Installer excludes** from every copy/compare/hash: files matching `test_*.py`, `__pycache__/` directories, and `*.pyc`.
- **Codex skills dir** is `$CODEX_HOME/skills` else `~/.codex/skills` — never `~/.agents/skills`. (Already correct in `install.py`; do not regress it.)
- **Public repo:** never introduce or retain the name of any private consumer repo. Use generic wording ("a private provisioning repo", "a downstream consumer").
- **Receipt filename:** `.ai-skills-install.json`, written at each agent **skills-dir root** (not inside a skill folder).
- **git workflow:** work on branch `claude/skills-installer-github-flow`; commit per task; do not open a PR or merge (the controller/user handles that).

---

### Task 1: `github-flow` prose skill + structure test

The first prose (no-`scaffold.py`) skill, with a structure test that validates its shape (there is no script to unit-test).

**Files:**
- Create: `skills/github-flow/SKILL.md`
- Create: `skills/github-flow/agents/openai.yaml`
- Create: `skills/github-flow/test_skill.py`

**Interfaces:**
- Produces: a discoverable skill directory `skills/github-flow/` (has `SKILL.md`, no `scaffold.py`). Later tasks rely on it being a valid skill with a subdirectory file (`agents/openai.yaml`) for whole-dir install coverage.

- [ ] **Step 1: Write the failing structure test**

Create `skills/github-flow/test_skill.py`:

```python
import re
from pathlib import Path

SKILL_DIR = Path(__file__).resolve().parent


def _frontmatter(text):
    m = re.match(r"^---\n(.*?)\n---\n", text, re.DOTALL)
    assert m, "SKILL.md must start with a YAML frontmatter block"
    body = m.group(1)
    fields = {}
    for key in ("name", "description"):
        km = re.search(rf"^{key}:\s*(.+)$", body, re.MULTILINE)
        fields[key] = km.group(1).strip().strip('"').strip() if km else ""
    return fields


def test_skill_md_exists():
    assert (SKILL_DIR / "SKILL.md").exists()


def test_frontmatter_name_matches_dir_and_has_description():
    fm = _frontmatter((SKILL_DIR / "SKILL.md").read_text(encoding="utf-8"))
    assert fm["name"] == "github-flow"
    assert len(fm["description"]) > 0


def test_is_prose_skill_no_scaffold():
    # github-flow is prose by design: no scaffold.py.
    assert not (SKILL_DIR / "scaffold.py").exists()


def test_agents_metadata_present():
    assert (SKILL_DIR / "agents" / "openai.yaml").exists()
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `python -m pytest skills/github-flow/test_skill.py -v`
Expected: FAIL — `SKILL.md` / `agents/openai.yaml` do not exist yet.

- [ ] **Step 3: Create `skills/github-flow/SKILL.md`**

Create `skills/github-flow/SKILL.md` with exactly this content:

```markdown
---
name: github-flow
description: "Use when the user asks Codex to commit, push, open a pull request, merge, ship, wrap up, publish, or clean up code changes in a git/GitHub repository. Enforce the user's preferred Feature Branch Workflow / GitHub Flow: branch, code and commit, pull request, review and checks, merge, return to main, pull, then delete the feature branch. Do not commit directly to main/master/default unless the user explicitly requests that exception."
---

# GitHub Flow

## Core Rule

Use Feature Branch Workflow / GitHub Flow for git publishing work.

Do not commit directly to `main`, `master`, or the repository default branch unless the user explicitly says to commit directly there. When the user says "merge", "ship", "wrap up", "commit this", or similar, interpret that as the full branch, PR, merge, and cleanup workflow unless they clearly ask for a narrower action.

## Workflow

1. Inspect state:
   - Run `git status --short --branch`.
   - Identify the current branch and default branch.
   - If there are unrelated user changes, preserve them and do not stage them accidentally.
2. Branch:
   - If on the default branch, create a descriptively named feature branch before committing.
   - If already on a feature branch, continue there unless it is clearly unrelated.
3. Commit:
   - Stage only intended files.
   - Run relevant tests/checks before or after committing based on repo norms and change risk.
   - Commit with a concise message that describes the net change.
4. Push and PR:
   - Push the feature branch with upstream tracking.
   - Open a pull request against the default branch.
   - Prefer repository PR templates when present.
   - Use a temp body file or `--body-file` for `gh pr create/edit` to avoid shell quoting problems.
5. Review and checks:
   - Summarize the PR URL, changed files, and verification.
   - If checks or review comments need attention, fix them on the same feature branch and update the PR.
6. Merge:
   - When the user asks to merge, merge the PR rather than bypassing it.
   - Use the repository's normal merge strategy if discoverable; otherwise prefer squash merge for small single-purpose branches unless the user or repo indicates otherwise.
7. Cleanup:
   - Switch back to the default branch.
   - Pull the latest default branch.
   - Delete the local feature branch.
   - Delete the remote feature branch when the PR merge did not already do so.
   - End with `git status --short --branch`.

## Safety

- Never use destructive commands such as `git reset --hard`, force-push, or branch deletion when unsure which branch contains unique work. Ask first.
- Never stage secrets, `.env` files, generated caches, or unrelated user edits.
- If network or GitHub CLI access is needed and sandboxed, request escalation with a narrow `gh` or `git push` prefix.
- If the repo has no remote or no GitHub PR path, stop after the local feature-branch commit and explain the missing piece.

## Current-Repo Recovery

If Codex already committed directly to the default branch by mistake and the commit has not been pushed:

1. Create a feature branch at the current commit.
2. Move the default branch back to its upstream or prior commit using a non-destructive branch update, avoiding loss of uncommitted changes.
3. Continue with push, PR, merge, and cleanup from the feature branch.
4. Explain the recovery clearly to the user.
```

- [ ] **Step 4: Create `skills/github-flow/agents/openai.yaml`**

Create `skills/github-flow/agents/openai.yaml` with exactly:

```yaml
interface:
  display_name: "GitHub Flow"
  short_description: "Use feature branches, PRs, merges, and branch cleanup"
  default_prompt: "Use GitHub Flow for this git task."
```

- [ ] **Step 5: Run the test to verify it passes**

Run: `python -m pytest skills/github-flow/test_skill.py -v`
Expected: PASS (4 tests).

- [ ] **Step 6: Commit**

```bash
git add skills/github-flow/
git commit -m "feat(skills): add github-flow prose skill + structure test"
```

---

### Task 2: Generalize `install.py` to whole-directory copy

Replace the fixed two-file copy with a recursive copy of the whole skill dir, excluding tests/caches, so skills with subdirectories (like `github-flow/agents/`) install fully.

**Files:**
- Modify: `scripts/install.py`
- Modify: `scripts/test_install.py`

**Interfaces:**
- Consumes: `discover_skills(skills_root)` (unchanged).
- Produces:
  - `runtime_files(skill_dir) -> list[Path]` — sorted **relative** paths of a skill's installable files (excludes `test_*.py`, `__pycache__`, `*.pyc`).
  - `install(skills_root, dests, names=None) -> dict` — now copies every runtime file (preserving subdirs) into each dest; `report["copied"]` is the list of destination file paths (strings).

- [ ] **Step 1: Write the failing tests**

Append to `scripts/test_install.py`:

```python
def test_install_copies_subdirectories(tmp_path):
    skills = tmp_path / "skills"
    (skills / "prose" / "agents").mkdir(parents=True)
    (skills / "prose" / "SKILL.md").write_text("s", encoding="utf-8")
    (skills / "prose" / "agents" / "openai.yaml").write_text("y", encoding="utf-8")
    dest = tmp_path / "claude"
    report = inst.install(skills, [dest])
    assert (dest / "prose" / "SKILL.md").read_text(encoding="utf-8") == "s"
    assert (dest / "prose" / "agents" / "openai.yaml").read_text(encoding="utf-8") == "y"
    assert len(report["copied"]) == 2  # SKILL.md + agents/openai.yaml


def test_runtime_files_excludes_tests_and_caches(tmp_path):
    skill = tmp_path / "s"
    (skill / "__pycache__").mkdir(parents=True)
    (skill / "SKILL.md").write_text("s", encoding="utf-8")
    (skill / "scaffold.py").write_text("c", encoding="utf-8")
    (skill / "test_scaffold.py").write_text("t", encoding="utf-8")
    (skill / "__pycache__" / "scaffold.cpython-312.pyc").write_text("x", encoding="utf-8")
    names = {p.as_posix() for p in inst.runtime_files(skill)}
    assert names == {"SKILL.md", "scaffold.py"}
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `python -m pytest scripts/test_install.py -v`
Expected: FAIL — `runtime_files` is not defined; `test_install_copies_subdirectories` fails (agents/ not copied).

- [ ] **Step 3: Add `runtime_files` and rewrite the copy loop**

In `scripts/install.py`, after the `RUNTIME_FILES = ("SKILL.md", "scaffold.py")` line (keep it — still used nowhere critical; you may delete it since it's now unused) add:

```python
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
```

Remove the now-unused `RUNTIME_FILES` constant. Then replace the body of `install()`'s copy loop. Change:

```python
    report = {"copied": []}
    for skill in skills:
        for dest_root in dests:
            dest = Path(dest_root) / skill.name
            dest.mkdir(parents=True, exist_ok=True)
            for fname in RUNTIME_FILES:
                src = skill / fname
                if src.exists():
                    shutil.copy2(src, dest / fname)
                    report["copied"].append(str(dest / fname))
    return report
```

to:

```python
    report = {"copied": []}
    for skill in skills:
        for dest_root in dests:
            dest = Path(dest_root) / skill.name
            for rel in runtime_files(skill):
                target = dest / rel
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(skill / rel, target)
                report["copied"].append(str(target))
    return report
```

- [ ] **Step 4: Run the tests to verify they pass**

Run: `python -m pytest scripts/test_install.py -v`
Expected: PASS — including the pre-existing `test_install_copies_runtime_files_not_tests` (a skill with `SKILL.md` + `scaffold.py` + `test_scaffold.py` still copies exactly 2 files × 2 dests = 4).

- [ ] **Step 5: Full suite + real github-flow install check**

Run: `python -m pytest -q`
Expected: PASS (all skills + scripts tests).

Then verify github-flow installs its subdir into a scratch dir:
Run: `python scripts/install.py github-flow --claude-dir "$TMPDIR/c" --codex-dir "$TMPDIR/x" && ls "$TMPDIR/c/github-flow/agents/openai.yaml"`
Expected: the `agents/openai.yaml` path exists under the scratch Claude dir. (On Windows PowerShell use `$env:TEMP` for a scratch path.)

- [ ] **Step 6: Commit**

```bash
git add scripts/install.py scripts/test_install.py
git commit -m "feat(install): copy whole skill dir (excl tests/caches), support subdirs"
```

---

### Task 3: `--check` dry-run drift report

Report per-skill install status (missing/current/stale) by byte comparison, copying nothing, with a non-zero exit on drift so consumers can gate.

**Files:**
- Modify: `scripts/install.py`
- Modify: `scripts/test_install.py`

**Interfaces:**
- Consumes: `discover_skills`, `runtime_files` (Task 2).
- Produces:
  - `_select_skills(skills_root, names) -> list[Path]` — the skill-selection + unknown-name validation extracted from `install()` (raises `ValueError` listing available names).
  - `check(skills_root, dests, names=None) -> dict` — `{"skills": {name: {dest_str: {"status": "missing"|"current"|"stale"}}}, "drift": bool}`. Copies nothing.
  - CLI: `install.py --check [names...]` prints per-skill status and returns `1` if any drift, else `0`.

- [ ] **Step 1: Write the failing tests**

Append to `scripts/test_install.py`:

```python
def test_check_reports_missing_then_current_then_stale(tmp_path):
    skills = tmp_path / "skills"
    _make_skill(skills, "alpha")
    dest = tmp_path / "claude"

    r1 = inst.check(skills, [dest])
    assert r1["skills"]["alpha"][str(dest)]["status"] == "missing"
    assert r1["drift"] is True

    inst.install(skills, [dest])
    r2 = inst.check(skills, [dest])
    assert r2["skills"]["alpha"][str(dest)]["status"] == "current"
    assert r2["drift"] is False

    (dest / "alpha" / "SKILL.md").write_text("mutated", encoding="utf-8")
    r3 = inst.check(skills, [dest])
    assert r3["skills"]["alpha"][str(dest)]["status"] == "stale"
    assert r3["drift"] is True


def test_check_cli_exit_codes(tmp_path, capsys):
    skills = tmp_path / "skills"
    _make_skill(skills, "alpha")
    dest = tmp_path / "claude"
    argv_check = ["--check", "--skills-root", str(skills),
                  "--claude-dir", str(dest), "--codex-dir", str(tmp_path / "x")]
    assert inst.main(argv_check) == 1          # missing -> drift -> exit 1
    inst.main(["--skills-root", str(skills),
               "--claude-dir", str(dest), "--codex-dir", str(tmp_path / "x")])
    assert inst.main(argv_check) == 0          # now installed -> exit 0


def test_check_unknown_skill_raises(tmp_path):
    skills = tmp_path / "skills"
    _make_skill(skills, "alpha")
    try:
        inst.check(skills, [tmp_path / "d"], names=["nope"])
    except ValueError as e:
        assert "nope" in str(e) and "alpha" in str(e)
    else:
        raise AssertionError("expected ValueError")
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `python -m pytest scripts/test_install.py -k check -v`
Expected: FAIL — `check` / `--check` not defined.

- [ ] **Step 3: Extract `_select_skills`, add `check`, wire `--check`**

In `scripts/install.py`, add `_select_skills` and refactor `install()` to use it. Replace the top of `install()`:

```python
def install(skills_root, dests, names=None) -> dict:
    skills = discover_skills(skills_root)
    if names:
        by_name = {p.name: p for p in skills}
        unknown = [n for n in names if n not in by_name]
        if unknown:
            available = ", ".join(sorted(by_name)) or "(none)"
            raise ValueError(
                f"unknown skill(s): {', '.join(unknown)}; available: {available}"
            )
        skills = [by_name[n] for n in names]
    report = {"copied": []}
```

with:

```python
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


def install(skills_root, dests, names=None) -> dict:
    skills = _select_skills(skills_root, names)
    report = {"copied": []}
```

Then add `check()`:

```python
def _classify(skill_dir, installed_dir) -> str:
    if not Path(installed_dir).exists():
        return "missing"
    for rel in runtime_files(skill_dir):
        inst_file = Path(installed_dir) / rel
        if not inst_file.exists():
            return "missing"
        if (Path(skill_dir) / rel).read_bytes() != inst_file.read_bytes():
            return "stale"
    return "current"


def check(skills_root, dests, names=None) -> dict:
    skills = _select_skills(skills_root, names)
    report = {"skills": {}, "drift": False}
    for skill in skills:
        per_dest = {}
        for dest_root in dests:
            status = _classify(skill, Path(dest_root) / skill.name)
            per_dest[str(dest_root)] = {"status": status}
            if status != "current":
                report["drift"] = True
        report["skills"][skill.name] = per_dest
    return report
```

In `main()`, add the flag (after the `names` positional argument definition):

```python
    parser.add_argument("--check", action="store_true",
                        help="Report install status (missing/current/stale); copy nothing.")
```

And branch before the install call. Replace:

```python
    dests = [Path(args.claude_dir), Path(args.codex_dir)]
    try:
        report = install(Path(args.skills_root), dests, args.names or None)
    except ValueError as e:
        print(f"error: {e}", file=sys.stderr)
        return 2
    for f in report["copied"]:
        print(f"installed {f}")
    print(f"done: {len(report['copied'])} files across {len(dests)} agent dirs")
    return 0
```

with:

```python
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
        report = install(Path(args.skills_root), dests, args.names or None)
    except ValueError as e:
        print(f"error: {e}", file=sys.stderr)
        return 2
    for f in report["copied"]:
        print(f"installed {f}")
    print(f"done: {len(report['copied'])} files across {len(dests)} agent dirs")
    return 0
```

- [ ] **Step 4: Run the tests to verify they pass**

Run: `python -m pytest scripts/test_install.py -v`
Expected: PASS (check tests + all pre-existing).

- [ ] **Step 5: Commit**

```bash
git add scripts/install.py scripts/test_install.py
git commit -m "feat(install): --check dry-run drift report with non-zero exit on drift"
```

---

### Task 4: Per-skill content-hash install receipt

Record what was installed — source git commit + a per-skill SHA-256 — in `.ai-skills-install.json` at each skills-dir root, and surface it in `--check`.

**Files:**
- Modify: `scripts/install.py`
- Modify: `scripts/test_install.py`

**Interfaces:**
- Consumes: `runtime_files` (Task 2), `_select_skills`, `check` (Task 3).
- Produces:
  - `skill_hash(skill_dir) -> str` — SHA-256 hex over the skill's runtime files (sorted `relpath` + bytes).
  - `source_commit(repo_root) -> str | None` — `git -C <repo_root> rev-parse HEAD`, or `None` if not a git checkout / git unavailable.
  - `install(skills_root, dests, names=None, commit=None, installed_at=None, write_receipt=True) -> dict` — now also writes `.ai-skills-install.json` to each dest root (merging with any existing receipt).
  - `check(...)` per-dest entries gain `"recordedHash"` (from the receipt, or `None`) and `"currentHash"`.

- [ ] **Step 1: Write the failing tests**

Append to `scripts/test_install.py`:

```python
import json


def test_install_writes_receipt_with_commit_and_per_skill_hash(tmp_path):
    skills = tmp_path / "skills"
    _make_skill(skills, "alpha")
    _make_skill(skills, "beta")
    dest = tmp_path / "claude"
    inst.install(skills, [dest], commit="deadbeef", installed_at="2026-07-19T00:00:00Z")
    receipt = json.loads((dest / ".ai-skills-install.json").read_text(encoding="utf-8"))
    assert receipt["commit"] == "deadbeef"
    assert receipt["installedAt"] == "2026-07-19T00:00:00Z"
    assert set(receipt["skills"]) == {"alpha", "beta"}
    assert len(receipt["skills"]["alpha"]["hash"]) == 64  # sha256 hex


def test_receipt_hash_is_per_skill_independent(tmp_path):
    skills = tmp_path / "skills"
    _make_skill(skills, "alpha")
    _make_skill(skills, "beta")
    dest = tmp_path / "claude"
    inst.install(skills, [dest])
    r1 = json.loads((dest / ".ai-skills-install.json").read_text(encoding="utf-8"))
    # change ONLY beta, reinstall, and confirm alpha's recorded hash is unchanged
    (skills / "beta" / "SKILL.md").write_text("beta CHANGED", encoding="utf-8")
    inst.install(skills, [dest])
    r2 = json.loads((dest / ".ai-skills-install.json").read_text(encoding="utf-8"))
    assert r2["skills"]["alpha"]["hash"] == r1["skills"]["alpha"]["hash"]
    assert r2["skills"]["beta"]["hash"] != r1["skills"]["beta"]["hash"]


def test_install_partial_merges_receipt(tmp_path):
    skills = tmp_path / "skills"
    _make_skill(skills, "alpha")
    _make_skill(skills, "beta")
    dest = tmp_path / "claude"
    inst.install(skills, [dest], names=["alpha"])
    inst.install(skills, [dest], names=["beta"])
    receipt = json.loads((dest / ".ai-skills-install.json").read_text(encoding="utf-8"))
    assert set(receipt["skills"]) == {"alpha", "beta"}  # beta run kept alpha


def test_source_commit_none_when_not_git(tmp_path):
    assert inst.source_commit(tmp_path) is None


def test_check_surfaces_recorded_hash(tmp_path):
    skills = tmp_path / "skills"
    _make_skill(skills, "alpha")
    dest = tmp_path / "claude"
    inst.install(skills, [dest])
    rep = inst.check(skills, [dest])
    entry = rep["skills"]["alpha"][str(dest)]
    assert entry["recordedHash"] == entry["currentHash"]
    assert entry["recordedHash"] is not None
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `python -m pytest scripts/test_install.py -k "receipt or source_commit or recorded" -v`
Expected: FAIL — `skill_hash`/`source_commit`/receipt not defined; `install` has no `commit` kwarg.

- [ ] **Step 3: Add hashing, commit lookup, receipt; wire into install + check**

In `scripts/install.py`, add imports at the top (with the existing imports):

```python
import hashlib
import json
import subprocess
```

Add helpers (near `runtime_files`):

```python
RECEIPT_NAME = ".ai-skills-install.json"


def skill_hash(skill_dir) -> str:
    h = hashlib.sha256()
    for rel in runtime_files(skill_dir):
        h.update(rel.as_posix().encode("utf-8"))
        h.update(b"\0")
        h.update((Path(skill_dir) / rel).read_bytes())
        h.update(b"\0")
    return h.hexdigest()


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
```

Change the `install()` signature and add the receipt write at the end:

```python
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
```

Enrich `check()`'s per-dest entry (replace the inner loop body):

```python
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
```

Finally, in `main()`, compute the commit + timestamp and pass them to `install()`. Add near the top of `main()` (after `repo_root = ...`):

```python
    from datetime import datetime, timezone
```

and change the install call in the non-`--check` branch:

```python
        report = install(Path(args.skills_root), dests, args.names or None,
                         commit=source_commit(repo_root),
                         installed_at=datetime.now(timezone.utc).isoformat())
```

- [ ] **Step 4: Run the tests to verify they pass**

Run: `python -m pytest scripts/test_install.py -v`
Expected: PASS (receipt tests + all pre-existing; the `check` status tests from Task 3 still pass since `["status"]` is still present).

- [ ] **Step 5: Full suite**

Run: `python -m pytest -q`
Expected: PASS (all tests).

- [ ] **Step 6: Commit**

```bash
git add scripts/install.py scripts/test_install.py
git commit -m "feat(install): per-skill content-hash receipt + --check surfaces it"
```

---

### Task 5: Docs + privacy scrub

Document prose skills / `--check` / versioning in the README, add the `github-flow` row, and remove every reference to any private consumer repo from the public repo.

**Files:**
- Modify: `README.md`
- Modify: `docs/superpowers/specs/2026-07-19-ai-skills-design.md`
- Modify: `docs/superpowers/plans/2026-07-19-script-driven-skills.md`

**Interfaces:** none (docs only).

- [ ] **Step 1: Update `README.md`**

Make these edits to `README.md`:

1. In the **Skills** table, add a row:

   ```markdown
   | [`github-flow`](skills/github-flow/SKILL.md) | Enforce Feature Branch Workflow / GitHub Flow: branch, commit, PR, merge, cleanup. Prose skill (no script). | yes (git/gh) |
   ```

2. Under the sentence describing skill layout, add a note that skills may be prose-only:

   ```markdown
   A skill is any `skills/<name>/` containing a `SKILL.md`. A `scaffold.py` is
   optional: **script-driven** skills bundle one (with tests); **prose** skills
   (like `github-flow`) are `SKILL.md` plus any support files (e.g. `agents/`).
   ```

3. In the **Install** section, replace the "runtime files — SKILL.md + scaffold.py" description with whole-dir wording:

   ```markdown
   Installs each skill's files — the **entire** `skills/<name>/` tree except
   `test_*.py` and `__pycache__` — into both agents' skill directories.
   ```

4. Update the "What gets installed" table to reflect whole-dir copy (source `skills/<name>/**` except `test_*.py`/`__pycache__` → `~/.claude/skills/<name>/…` and `$CODEX_HOME/skills/<name>/…`).

5. Add a short **Check / versioning** subsection under Install:

   ```markdown
   ### Check what's installed

   `python scripts/install.py --check [names…]` reports each skill as
   `missing` / `current` / `stale` (byte comparison) and exits non-zero if any
   drift — copies nothing. Install writes a receipt `.ai-skills-install.json`
   in each skills dir recording the source git commit and a per-skill SHA-256,
   so you can see exactly which revision of each skill a machine has.
   ```

6. **Remove the private-consumer reference.** In the "Consuming from another repo" section, replace the bullet that names a specific private provisioning repo with generic wording, e.g.:

   ```markdown
   - A **private provisioning repo** can clone this repo at a pinned commit and
     run `scripts/install.py` (or `--check` first) in its plan→apply flow.
   - A **public docs repo** can link here instead of holding skill copies.
   ```

- [ ] **Step 2: Scrub the historical spec + plan**

In `docs/superpowers/specs/2026-07-19-ai-skills-design.md` and `docs/superpowers/plans/2026-07-19-script-driven-skills.md`, replace every occurrence of the private provisioning repo's name with a generic phrase ("a private provisioning repo" / "a downstream consumer"). Preserve surrounding meaning; only the name changes.

- [ ] **Step 3: Verify no private-repo name remains**

Run: `grep -rni "windows-setup" . --include="*.md" | grep -v "/.git/"`
Expected: **no output** (every reference removed).

Also confirm no other private identifiers leaked:
Run: `grep -rniE "homelab|cookenas|jtcooke|frankenleg\\.com" . | grep -v "/.git/"`
Expected: no output.

- [ ] **Step 4: Full suite still green (docs-only, sanity)**

Run: `python -m pytest -q`
Expected: PASS (unchanged).

- [ ] **Step 5: Commit**

```bash
git add README.md docs/superpowers/
git commit -m "docs: prose skills, --check, versioning; scrub private-consumer name"
```

---

## Self-Review

**Spec coverage:**
- §1 github-flow prose skill + structure test → Task 1. ✓
- §2 generalized whole-dir installer (excl tests/caches, subdirs) → Task 2. ✓
- §3 `--check` byte-compare drift + non-zero exit → Task 3. ✓
- §4 receipt: commit SHA + per-skill hash; `--check` surfaces it → Task 4. ✓
- §5 README (prose skills, whole-dir, --check, versioning, github-flow row) + scrub private name from README/old spec/old plan → Task 5. ✓
- "no hand-maintained VERSION file" → Task 4 uses commit + hash only; no VERSION created anywhere. ✓
- Codex dir stays `$CODEX_HOME/skills`/`~/.codex/skills` (not `~/.agents`) → untouched by all tasks; Global Constraints call it out. ✓

**Placeholder scan:** no TBD/TODO; every code step shows complete code; the github-flow SKILL.md is reproduced in full; test bodies are concrete. ✓

**Type consistency:** `runtime_files` returns sorted relative `Path`s (Task 2), consumed identically by `_classify`, `skill_hash` (Task 4). `install(..., commit=None, installed_at=None, write_receipt=True)` (Task 4) is a superset of the Task 2/3 signature — existing 2-positional-arg calls still valid. `check()` returns `{"skills": {name: {dest: {"status", "recordedHash", "currentHash"}}}, "drift"}` — Task 3 defines `"status"`, Task 4 adds the two hash keys without removing it, so Task 3's assertions on `["status"]` still hold. `_select_skills` (Task 3) is used by both `install` and `check`. `RECEIPT_NAME` constant consistent across `_read_receipt`/`_write_receipt`/tests. ✓
