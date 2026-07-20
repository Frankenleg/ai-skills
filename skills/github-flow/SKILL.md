---
name: github-flow
description: "Use when the user asks to commit, push, publish, open or update a pull request, merge, ship, wrap up, or clean up code changes in a git/GitHub repository. Apply Feature Branch Workflow / GitHub Flow while limiting work to the requested stage: never treat commit, ship, wrap up, push, publish, or PR creation as authorization to merge. Do not commit directly to the repository default branch unless the user explicitly requests that exception."
---

# GitHub Flow

## Authorization boundary

Use a feature branch for git publishing work. Do not commit directly to the
repository default branch unless the user explicitly requests that exception.

Perform only the requested stage and its prerequisites:

- **Commit**: create or use the feature branch, verify the change, and commit.
  Do not push, create a PR, merge, or clean up unless separately requested.
- **Push** or **publish**: push the feature branch and verify the remote ref.
  Create or update a PR only when requested. Do not merge.
- **Open**, **create**, or **update a PR**: ensure the intended commits are
  pushed, then create or update the PR. Do not merge.
- **Ship** or **wrap up**: absent a narrower repository or user definition,
  prepare the work through an open PR, report it ready, and stop before merge.
- **Merge**: merge and clean up only after an explicit user instruction to
  merge. Earlier approval to commit, push, publish, ship, wrap up, or open a PR
  is not merge authorization.

## Native command gate

Check the exit code after every `git` and `gh` command before running a
dependent command or mutation. In PowerShell, explicitly inspect
`$LASTEXITCODE`; `$ErrorActionPreference` alone does not catch native command
failures. Stop and report an unexpected nonzero exit after operations including
push, PR create/edit, merge, fetch/pull, and branch deletion. Proceed after a
nonzero exit only when this skill defines that exact code as an expected state.
Guard each native call immediately, for example `& git status --short --branch`
followed by `if ($LASTEXITCODE -ne 0) { throw "git status failed" }`. Do not
execute or present a sequence of unguarded native commands.

## Inspect and preserve state

1. Run `git status --short --branch` and identify intended versus unrelated
   changes. Stage only intended paths; never stage secrets, `.env` files,
   generated caches, or unrelated edits.
2. Read user and repository instructions before choosing branch, remote, base,
   checks, or merge strategy.
3. Never automatically stash, discard, or commit unrelated changes. If they
   prevent a safe branch switch, stop and ask the user unless a separate
   worktree or another clearly safe method preserves the original worktree
   unchanged.

## Select remotes and the default branch

Treat the base remote (the integration repository) and push remote (the feature
branch destination) as separate roles.

1. Honor an explicit user or repository choice for either remote.
2. Reuse the base/head repositories of an existing PR for the same work.
3. With exactly one remote, use it for both roles when it is writable.
4. With multiple remotes and no controlling instruction or existing PR, ask
   which is the base and which receives the feature branch. Do not assume that
   `origin`, `upstream`, or the current tracking remote has either role.
5. With no remotes, allow local branch and commit work, but stop before push or
   PR operations and report that no publication path exists. If instructions do
   not identify the default branch or confirm that the current branch is a
   feature branch, ask before committing. Do not infer a default branch from a
   local `main` or `master` name alone.

After selecting the base remote, discover its default branch by using the first
successful, unambiguous source in this exact order:

1. An explicit user or repository instruction.
2. `git symbolic-ref --quiet --short refs/remotes/<base-remote>/HEAD`.
3. GitHub's `defaultBranchRef` for the repository identified by the base remote,
   queried with `gh repo view --json defaultBranchRef`.
4. The `HEAD branch` reported by `git remote show <base-remote>`.
5. Ask the user if every source is absent, invalid, or ambiguous.

Validate that the result names a real branch in the selected base repository.
Do not guess from conventional names or skip directly to a lower-precedence
source. For `git symbolic-ref --quiet`, treat exit 1 as the expected "not a
symbolic ref" result and continue; treat other nonzero exits as failures. For a
GitHub remote, a nonzero `gh repo view` is an operational failure to report, not
evidence that `defaultBranchRef` is absent.

Before any `gh` PR operation, classify the selected base remote from its URL and
configured GitHub hosts. A missing remote or a clearly non-GitHub host means
there is no GitHub PR path. Once the remote is identified as GitHub, treat
authentication, authorization, network, API, and validation errors as failed
GitHub operations; never relabel them as "no remote" or "no PR path."

## Choose or create the feature branch

Use branch naming precedence in this order:

1. An explicit user branch name.
2. Repository naming instructions, including any required agent prefix.
3. An existing branch clearly associated with the same work.
4. `<configured-agent-prefix>/<short-kebab-description>` when a prefix is
   configured; otherwise `feature/<short-kebab-description>`.

For the fallback description, lowercase the task summary, replace each run of
non-alphanumeric characters with one hyphen, and trim leading/trailing hyphens.
If the resulting ref already exists for unrelated work, append `-2`, `-3`, and
so on using the first available name. If currently on the default branch,
create and switch to the feature branch before committing.

## Verify, commit, and push

1. Run the relevant tests and checks for the change and repository.
2. Stage only intended files and review the staged diff.
3. Commit with a concise message describing the net change.
4. When push is authorized, push with upstream tracking to the selected push
   remote.
5. Compare `git rev-parse HEAD` with the object ID returned by
   `git ls-remote <push-remote> refs/heads/<feature-branch>`. Stop if the pushed
   branch does not match local `HEAD`.

## Create or update a PR idempotently

Before `gh pr create`, query all PR states in the base repository for the exact
head owner and branch with
`gh pr list --repo <base-repository> --head <head-owner>:<feature-branch>
--state all` and inspect each PR's number, URL, state, base branch, and head
object ID.

- If exactly one open PR exists, verify that it targets the discovered default
  branch, then edit it when metadata changed or report its existing URL. Do not
  create a duplicate.
- If a matching PR is merged or closed, report it and ask before creating a new
  PR for the same head branch.
- If multiple PRs make the intended one ambiguous, stop and ask.
- Only when none exists, run `gh pr create --base <default-branch>`.

After creation or update, use `gh pr view` to confirm that the PR's head object
ID matches the pushed branch and its `baseRefName` equals the discovered default
branch.

Create the PR body in a securely created, uniquely named OS temporary file
(for example, `New-TemporaryFile` or `mktemp`). Record its exact path, pass that
path via `gh pr create/edit --body-file`, and remove that exact file in a
`finally`-style cleanup on success or failure. Never use a predictable shared
filename or wildcard cleanup. Do not substitute `--fill` or an inline body for
the required body-file lifecycle.

## Stage postconditions

Do not report a requested stage complete until its postcondition holds:

- **Commit**: the intended commit exists on the correct feature branch, tests
  have passed as required, and unrelated user changes remain preserved.
- **Push/publish**: the push remote's feature ref object ID equals local `HEAD`.
- **PR**: exactly one intended open PR exists, its `baseRefName` is the
  discovered default branch, its head object ID equals the pushed ref, and the
  exact PR body temporary file has been removed.
- **Merge/cleanup**: apply all gates and final-state checks in the following
  sections; a successful merge with blocked cleanup is not complete cleanup and
  must be reported as such.

## Review and merge

Before merging, require all of these gates:

- The user has explicitly instructed the agent to merge this PR.
- Relevant local tests pass and every required GitHub check is successful, not
  pending or skipped unexpectedly.
- The PR is open, targets the discovered default branch, and its recorded head
  object ID matches both local `HEAD` and the pushed feature ref.
- Intended user changes are committed or explicitly preserved and reported.

Choose the merge strategy deterministically:

1. Follow explicit user or repository instructions and repository rules.
2. Preserve a strategy already selected by the user or by configured
   auto-merge.
3. Otherwise, use squash for a small, single-purpose branch.
4. If the branch is not small and single-purpose, or the choice remains
   ambiguous, ask before merging.

Query the repository's allowed merge methods before invoking `gh pr merge`.
Never silently substitute another strategy if the selected one is unavailable
or fails, and never change strategy after checks or approval without asking.

## Clean up after a verified merge

Handle merge commits, squash merges, rebase merges, and an already-deleted
remote branch with the same ordered procedure:

1. Use `gh pr view` to confirm state `MERGED`, the expected `baseRefName`, the
   merged PR's `headRefOid`, and its resulting `mergeCommit` object ID. Do not
   clean up an unmerged or ambiguous PR.
2. Confirm the local feature tip still equals the merged PR's `headRefOid`; stop
   if local-only commits appeared after the PR was merged.
3. Switch to the default branch without stashing or discarding unrelated
   changes. Fetch and update it from the selected base remote using a
   fast-forward-only update.
4. Verify that `mergeCommit` is an ancestor of the updated default branch. This
   proves the PR's resulting merge or squash commit is present even when the
   original feature commits are not ancestors.
5. Check the remote feature ref with
   `git ls-remote --exit-code --heads <push-remote> refs/heads/<feature-branch>`.
   Exit 0 means it exists and may now be deleted; exit 2 means it is already
   absent and is success. Treat every other nonzero exit as a failure. After a
   deletion, repeat the query and require exit 2 before deleting locally.
6. Delete the local feature branch last. Try `git branch -d` first. If it fails
   solely because a verified squash or rebase left the original commits
   unmerged, permit `git branch -D` only after steps 1-5 and the `headRefOid`
   equality check all succeeded. Treat a verified already-absent local branch as
   successful cleanup.
7. End on the updated default branch. Run `git status --short --branch` and
   report the PR URL, merge strategy, verification results, remote/local branch
   cleanup (including "already absent"), and every preserved user change.

## Recover an accidental local commit on the default branch

Use this recovery only when the accidental commit has not been pushed:

1. Record the default branch, its verified upstream, the accidental commit ID,
   and snapshots of uncommitted state: porcelain status with all untracked
   files, staged and unstaged binary diffs, and hashes of untracked file
   contents.
2. Fetch the relevant remotes. Verify that no remote branch contains the
   accidental commit and that the verified default upstream resolves to the
   intended pre-commit point. If the commit was pushed or the upstream is
   missing or ambiguous, stop and ask.
3. Create and switch to the recovery feature branch at the current commit
   first. Confirm its `HEAD` equals the recorded accidental commit.
4. While the default branch is inactive, move only its branch ref to the
   verified upstream with `git branch -f <default-branch> <verified-upstream>`.
   Never use `git reset --hard`.
5. Confirm the recovery branch still points to the accidental commit, the
   default branch now equals its verified upstream, and every recorded status,
   diff, and untracked-file hash is unchanged.
6. Continue only through the stage the user authorized and explain the recovery.
