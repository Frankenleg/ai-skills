import re
from pathlib import Path

SKILL_DIR = Path(__file__).resolve().parent


def _skill_text():
    return (SKILL_DIR / "SKILL.md").read_text(encoding="utf-8")


def _norm(text):
    # Collapse whitespace and lowercase so assertions test intent, not the
    # exact prose reflow/line-wrapping. Rewording the same idea should not
    # break these; changing the meaning should.
    return re.sub(r"\s+", " ", text).lower()


def _frontmatter(text):
    m = re.match(r"^---\n(.*?)\n---\n", text, re.DOTALL)
    assert m, "SKILL.md must start with a YAML frontmatter block"
    body = m.group(1)
    fields = {}
    for key in ("name", "description"):
        km = re.search(rf"^{key}:\s*(.+)$", body, re.MULTILINE)
        fields[key] = km.group(1).strip().strip('"').strip() if km else ""
    return fields


# --- structure ------------------------------------------------------------

def test_skill_md_exists():
    assert (SKILL_DIR / "SKILL.md").exists()


def test_is_prose_skill_no_scaffold():
    # github-flow is prose by design: no scaffold.py.
    assert not (SKILL_DIR / "scaffold.py").exists()


def test_agents_metadata_present():
    assert (SKILL_DIR / "agents" / "openai.yaml").exists()


def test_skill_md_is_agent_neutral():
    # Installs to both Claude Code and Codex, so SKILL.md must not hardcode a
    # single agent's name. Agent-specific bits go in agents/<agent>.yaml.
    text = _skill_text().lower()
    for agent in ("codex", "claude"):
        assert agent not in text, (
            f"github-flow is cross-agent; SKILL.md must not name {agent!r}"
        )


def test_stays_light():
    # Decision (2026-07-19): this skill stays proportionate — invariants over
    # exhaustive ceremony. Locking a line budget so a future rewrite that
    # balloons it fails here instead of silently drifting.
    lines = _skill_text().splitlines()
    assert len(lines) <= 140, f"SKILL.md grew to {len(lines)} lines; keep it light"


# --- frontmatter / trigger ------------------------------------------------

def test_frontmatter_name_and_agent_neutral_boundary_trigger():
    fm = _frontmatter(_skill_text())
    assert fm["name"] == "github-flow"
    desc = fm["description"].lower()
    assert len(desc) > 0
    # The trigger encodes the do-only-what-was-asked / not-merge boundary.
    assert "authorization to merge" in desc
    assert "default branch" in desc


# --- behavioral invariants (normalized: reword-safe) ----------------------

def test_authorization_boundary_separates_stages_from_merge():
    n = _norm(_skill_text())
    assert "authorization to merge" in n
    assert "only after an explicit instruction to merge" in n
    # Each non-merge stage is named as its own step.
    for stage in ("commit", "push", "publish", "ship", "wrap up", "open"):
        assert stage in n


def test_never_commit_directly_to_default_branch():
    n = _norm(_skill_text())
    assert "never commit directly to" in n
    assert "default branch" in n
    assert "unless" in n


def test_merge_requires_explicit_instruction_and_green_checks():
    n = _norm(_skill_text())
    assert "explicitly told you to merge" in n
    assert "required github check is green" in n


def test_merge_default_is_merge_commit_not_squash():
    # Regression lock for PR #7's decision: the fallback merge strategy is a
    # merge commit, and squash/rebase is opt-in only. This is exactly the kind
    # of decision that got silently reverted when regenerated from prose alone.
    n = _norm(_skill_text())
    assert "default to a merge commit" in n
    assert "squash or rebase only when" in n
    # Guard against reverting the fallback to squash-by-default.
    assert "use squash for a small" not in n
    assert "otherwise, use squash" not in n


def test_unrelated_changes_are_preserved():
    n = _norm(_skill_text())
    assert "auto-stash" in n
    assert "unrelated changes" in n
    assert "stop and ask" in n


def test_pr_creation_is_idempotent():
    n = _norm(_skill_text())
    assert "existing pr" in n
    assert "duplicate" in n


def test_pr_body_uses_template_and_body_file():
    n = _norm(_skill_text())
    assert "pr template" in n
    assert "--body-file" in n


def test_push_is_verified_landed():
    n = _norm(_skill_text())
    assert "confirm the remote branch now matches local `head`" in n


def test_cleanup_returns_to_default_and_tolerates_already_deleted():
    n = _norm(_skill_text())
    assert "already gone is success" in n
    assert "fast-forward it from the base remote" in n


def test_recovery_is_non_destructive():
    n = _norm(_skill_text())
    assert "git branch -f" in n
    assert "never `git reset --hard`" in n
