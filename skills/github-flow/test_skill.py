import re
from pathlib import Path

SKILL_DIR = Path(__file__).resolve().parent


def _skill_text():
    return (SKILL_DIR / "SKILL.md").read_text(encoding="utf-8")


def _section(text, heading):
    marker = f"## {heading}\n"
    assert marker in text, f"missing section: {heading}"
    section = text.split(marker, 1)[1]
    return section.split("\n## ", 1)[0]


def _assert_in_order(text, *needles):
    positions = [text.index(needle) for needle in needles]
    assert positions == sorted(positions), (
        f"expected ordered contract: {' -> '.join(needles)}"
    )


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
    fm = _frontmatter(_skill_text())
    assert fm["name"] == "github-flow"
    assert len(fm["description"]) > 0
    assert "never treat commit, ship, wrap up, push, publish, or PR creation" in fm[
        "description"
    ]


def test_is_prose_skill_no_scaffold():
    # github-flow is prose by design: no scaffold.py.
    assert not (SKILL_DIR / "scaffold.py").exists()


def test_agents_metadata_present():
    assert (SKILL_DIR / "agents" / "openai.yaml").exists()


def test_skill_md_is_agent_neutral():
    # github-flow installs to both Claude Code and Codex, so its SKILL.md
    # (trigger + body) must not hardcode a single agent's name. Agent-specific
    # metadata belongs in agents/<agent>.yaml, not here.
    text = _skill_text().lower()
    for agent in ("codex", "claude"):
        assert agent not in text, (
            f"github-flow is cross-agent; SKILL.md must not name {agent!r}"
        )


def test_only_explicit_merge_authorizes_merge():
    section = _section(_skill_text(), "Authorization boundary")
    assert "only after an explicit user instruction to\n  merge" in section
    assert "Commit**: create or use the feature branch" in section
    assert "Do not push, create a PR, merge, or clean up" in section
    assert "Push** or **publish**" in section
    assert "Create or update a PR only when requested. Do not merge." in section
    assert "Ship** or **wrap up**" in section
    assert "stop before merge" in section
    assert "is not merge authorization" in section
    assert not re.search(
        r'(?:commit|ship|wrap up)[^\n]{0,100}full[^\n]{0,100}merge',
        section,
        re.IGNORECASE,
    )


def test_native_commands_require_explicit_exit_code_gates():
    section = _section(_skill_text(), "Native command gate")
    assert "$LASTEXITCODE" in section
    assert "$LASTEXITCODE -ne 0" in section
    assert "after every `git` and `gh` command" in section
    for operation in ("push", "PR create/edit", "merge", "branch deletion"):
        assert operation in section
    assert "Stop and report an unexpected nonzero exit" in section
    assert "Do not\nexecute or present a sequence of unguarded native commands" in section


def test_unrelated_changes_are_never_implicitly_mutated():
    section = _section(_skill_text(), "Inspect and preserve state")
    assert "Never automatically stash, discard, or commit unrelated changes" in section
    assert "stop and ask the user" in section
    assert "separate\n   worktree" in section


def test_remote_and_default_branch_discovery_are_deterministic():
    section = _section(_skill_text(), "Select remotes and the default branch")
    assert "base remote" in section and "push remote" in section
    assert "With multiple remotes" in section
    assert "With no remotes" in section
    assert "ask before committing" in section
    normalized = re.sub(r"\s+", " ", section)
    assert "Do not infer a default branch from a local `main` or `master`" in normalized
    _assert_in_order(
        section,
        "An explicit user or repository instruction.",
        "refs/remotes/<base-remote>/HEAD",
        "defaultBranchRef",
        "git remote show <base-remote>",
        "Ask the user",
    )
    assert "treat exit 1 as the expected" in section
    assert "Do not guess from conventional names or skip directly" in section


def test_github_failures_are_not_misclassified_as_missing_pr_path():
    section = _section(_skill_text(), "Select remotes and the default branch")
    assert "classify the selected base remote from its URL" in section
    assert "clearly non-GitHub host" in section
    for failure in ("authentication", "authorization", "network", "validation"):
        assert failure in section
    assert 'never relabel them as "no remote" or "no PR path."' in section


def test_branch_naming_honors_precedence_and_has_deterministic_fallback():
    section = _section(_skill_text(), "Choose or create the feature branch")
    _assert_in_order(
        section,
        "An explicit user branch name.",
        "Repository naming instructions",
        "An existing branch clearly associated",
        "<configured-agent-prefix>/<short-kebab-description>",
    )
    assert "replace each run of\nnon-alphanumeric characters with one hyphen" in section
    assert "append `-2`, `-3`, and\nso on" in section


def test_push_verification_requires_remote_ref_to_match_local_head():
    section = _section(_skill_text(), "Verify, commit, and push")
    assert "git rev-parse HEAD" in section
    assert "git ls-remote <push-remote> refs/heads/<feature-branch>" in section
    assert "Stop if the pushed\n   branch does not match local `HEAD`." in section


def test_pr_creation_is_idempotent_for_every_existing_pr_state():
    section = _section(_skill_text(), "Create or update a PR idempotently")
    _assert_in_order(
        section,
        "Before `gh pr create`",
        "gh pr list",
        "--repo <base-repository>",
        "--head <head-owner>:<feature-branch>",
        "--state all",
        "Only when none exists",
    )
    assert "If exactly one open PR exists" in section
    assert "Do not\n  create a duplicate." in section
    assert "merged or closed" in section
    assert "If multiple PRs" in section
    assert "Only when none exists" in section


def test_pr_body_temp_file_has_exact_success_and_failure_cleanup():
    section = _section(_skill_text(), "Create or update a PR idempotently")
    assert "securely created, uniquely named OS temporary file" in section
    assert "--body-file" in section
    assert "remove that exact file" in section
    assert "on success or failure" in section
    assert "Never use a predictable shared\nfilename or wildcard cleanup." in section
    assert "Do not substitute `--fill` or an inline body" in section


def test_each_requested_stage_has_an_explicit_postcondition():
    section = _section(_skill_text(), "Stage postconditions")
    assert "intended commit exists on the correct feature branch" in section
    assert "feature ref object ID equals local `HEAD`" in section
    assert "exactly one intended open PR exists" in section
    assert "`baseRefName` is the\n  discovered default branch" in section
    assert "exact PR body temporary file has been removed" in section
    assert "successful merge with blocked cleanup is not complete cleanup" in section


def test_merge_gates_and_strategy_selection_are_deterministic():
    section = _section(_skill_text(), "Review and merge")
    assert "explicitly instructed the agent to merge this PR" in section
    assert "every required GitHub check is successful" in section
    assert "local `HEAD` and the pushed feature ref" in section
    _assert_in_order(
        section,
        "Follow explicit user or repository instructions",
        "Preserve a strategy already selected",
        "use squash for a small, single-purpose branch",
        "ask before merging",
    )
    assert "Never silently substitute another strategy" in section
    assert "never change strategy after checks or approval" in section


def test_cleanup_handles_squash_and_already_deleted_remote_branch_safely():
    section = _section(_skill_text(), "Clean up after a verified merge")
    _assert_in_order(
        section,
        "confirm state `MERGED`",
        "local feature tip still equals",
        "Switch to the default branch",
        "Verify that `mergeCommit` is an ancestor",
        "git ls-remote --exit-code --heads",
        "Delete the local feature branch last",
    )
    assert "exit 2 means it is already\n   absent and is success" in section
    assert "repeat the query and require exit 2" in section
    assert "permit `git branch -D` only after steps 1-5" in section
    assert "`headRefOid`\n   equality check all succeeded" in section
    assert "verified already-absent local branch" in section


def test_cleanup_postconditions_end_on_updated_default_and_report_preserved_work():
    section = _section(_skill_text(), "Clean up after a verified merge")
    assert "End on the updated default branch" in section
    assert "git status --short --branch" in section
    assert "every preserved user change" in section


def test_accidental_default_commit_recovery_is_ordered_and_non_destructive():
    section = _section(
        _skill_text(), "Recover an accidental local commit on the default branch"
    )
    _assert_in_order(
        section,
        "Verify that no remote branch contains the\n   accidental commit",
        "Create and switch to the recovery feature branch",
        "Confirm its `HEAD` equals the recorded accidental commit",
        "git branch -f <default-branch> <verified-upstream>",
        "Confirm the recovery branch still points to the accidental commit",
    )
    assert "Never use `git reset --hard`." in section
    assert "every recorded status,\n   diff, and untracked-file hash is unchanged" in section
