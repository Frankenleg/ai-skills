# Decision records

Non-obvious decisions for this repo, recorded here (not only in an agent's
memory) so both Claude Code and Codex share one source of truth. Append a new
dated entry at the bottom; never rewrite history. When a decision has a testable
surface, lock it with a test and cite it under **Locked by**.

Format per entry: **Decision** / **Reason** / **Alternatives rejected** /
**Locked by**.

---

## 2026-07-19 — Codex skills install to `~/.codex/skills`, not `~/.agents/skills`

**Decision:** `scripts/install.py` installs Codex skills to `$CODEX_HOME/skills`
(default `~/.codex/skills`).
**Reason:** Codex discovers skills there per its bundled `skill-creator` /
`skill-installer`. `~/.agents/` is the Codex *plugin* path
(`~/.agents/plugins/marketplace.json`), a different concept — skills placed there
are never loaded.
**Alternatives rejected:** `~/.agents/skills` (the original default; skills were
silently not discovered).
**Locked by:** `scripts/test_install.py::test_default_codex_dir_*`.

## 2026-07-19 — Default merge strategy is a merge commit

**Decision:** When no repo/user strategy is configured, merge PRs with a merge
commit (`--merge`); squash/rebase only when explicitly indicated.
**Reason:** Matches the maintainer's cross-repo preference (also recorded in the
global `~/.codex/AGENTS.md` git-workflow section, which overrides skill defaults).
**Alternatives rejected:** squash-by-default (a Codex rewrite reverted to this;
it contradicted the stated preference).
**Locked by:** `skills/github-flow/test_skill.py::test_merge_default_is_merge_commit_not_squash`.

## 2026-07-19 — Skills stay light, cross-platform, and agent-neutral

**Decision:** A `SKILL.md` carries no single-agent or single-shell assumptions
(agent-specific bits live in `agents/<agent>.yaml`), and scales rigor to risk
rather than adding exhaustive ceremony.
**Reason:** These skills install to both agents on any OS; heavy, agent- or
shell-specific prose is a maintenance and portability liability. (`github-flow`
was rebalanced 235 → 102 lines on this basis.)
**Alternatives rejected:** exhaustive per-command contracts; PowerShell-specific
guidance in shared skills.
**Locked by:** `skills/github-flow/test_skill.py::test_stays_light` and
`::test_skill_md_is_agent_neutral`.

## 2026-07-19 — Record decisions in the repo; encode testable ones as tests

**Decision:** Non-obvious decisions go in this file (and conventions in
`AGENTS.md`); memory only caches pointers. Decisions with a testable surface are
also locked with a test.
**Reason:** Per-agent memories are mutually invisible, so knowledge kept only in
memory does not cross between Claude Code and Codex. A red test surfaces a
reverted decision to whichever agent touches it, regardless of its context.
**Alternatives rejected:** relying on agent memory or commit messages to carry
decisions across agents.
**Locked by:** convention (this file) + `AGENTS.md` conventions section.

## 2026-07-19 — Scaffolders seed `docs/decisions.md` into every new project

**Decision:** `new-project` and `new-git-project` both create a
`docs/decisions.md` stub (only if absent) alongside `AGENTS.md`/`CLAUDE.md`, so a
new repo starts with the decision log in place. `new-git-project` includes it in
the initial commit.
**Reason:** Makes the "record decisions in the repo" convention automatic for new
projects rather than relying on someone remembering to create the file.
**Alternatives rejected:** documenting the convention only (no seed); a shared
helper between the two skills (they are standalone by design, so the template is
duplicated in each `scaffold.py`).
**Locked by:** `skills/new-project/test_scaffold.py::test_seeds_decisions_log_stub`,
`skills/new-git-project/test_scaffold.py::test_seeds_decisions_log_stub`.

## 2026-07-19 — Enable CI (GitHub Actions pytest)

**Decision:** Run `pytest` in GitHub Actions on every push and PR, across
Linux + Windows and Python 3.9/3.12 (`.github/workflows/ci.yml`). Supersedes the
design spec's "CI: deferred."
**Reason:** Decision-locking tests only protect a decision if they actually run.
CI runs them automatically on every PR from either agent, so a silently reverted
decision shows a red check instead of landing unnoticed. The Linux+Windows matrix
also guards the cross-platform LF/line-ending behavior.
**Alternatives rejected:** relying on contributors/agents to run pytest locally;
single-OS CI (would miss Windows line-ending regressions).
**Locked by:** the workflow itself. NOTE: making a failed check *block* merges
also requires branch protection on `main` (a GitHub repo setting: require the CI
status check to pass) — a manual step outside the repo.
