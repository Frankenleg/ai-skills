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
