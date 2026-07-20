---
name: github-flow
description: "Use when the user asks to commit, push, publish, open or update a pull request, merge, ship, wrap up, or clean up code changes in a git/GitHub repository. Apply Feature Branch Workflow / GitHub Flow, doing only the stage the user asked for: commit, push, publish, ship, wrap up, and PR creation authorize that step only — never as authorization to merge. Do not commit directly to the repository default branch unless the user explicitly requests it."
---

# GitHub Flow

Do publishing work on a feature branch, one stage at a time. Scale rigor to
risk: verify the irreversible steps (push, merge, branch moves, deletion) and
keep the routine ones (status, commit) light. Before a destructive or dependent
step, confirm the previous command actually succeeded (check its exit status)
rather than chaining blindly.

## Authorization boundary

Perform only the requested stage and its prerequisites — do not escalate:

- **Commit** — use or create the feature branch, verify the change, commit. Do
  not push, open a PR, merge, or clean up unless separately asked.
- **Push / publish** — push the feature branch. Open or update a PR only when
  asked. Do not merge.
- **Open / update a PR** — ensure the intended commits are pushed, then create
  or update the PR. Do not merge.
- **Ship / wrap up** — take the work through an open, ready PR and stop there.
  Report it ready; do not merge.
- **Merge** — merge and clean up only after an explicit instruction to merge.
  Prior approval to commit, push, publish, ship, wrap up, or open a PR is not
  authorization to merge.

Never commit directly to `main`/`master`/the default branch unless the user
explicitly asks for that exception.

## Branch and commit

1. Run `git status --short --branch`. Stage only intended paths. Never stage
   secrets, `.env` files, caches, or unrelated edits, and never auto-stash,
   discard, or commit unrelated changes — if they block a safe branch switch,
   stop and ask (or use a separate worktree that leaves the current one intact).
2. If on the default branch, create a feature branch first. Name it by the first
   that applies: an explicit user name; the repo's naming rule / required agent
   prefix; an existing branch for the same work; else a short kebab-case summary
   of the change.
3. Run the change's relevant tests/checks, then commit with a concise message
   describing the net change.

## Push and PR

1. Push the feature branch with upstream tracking, then confirm the remote
   branch now matches local `HEAD`.
2. Before creating a PR, check for an existing PR for this branch and reuse it:
   update the open one instead of opening a duplicate. If a prior PR for this
   branch is merged/closed, or multiple make the target ambiguous, stop and ask.
   Otherwise open the PR against the default branch.
3. Build the PR body from the repo's PR template when present; otherwise a
   concise summary plus a verification section, with any template placeholders
   resolved. Pass it via `--body-file` (write to a temp file, then remove it) to
   avoid shell-quoting problems — don't hand-inline a multi-line body.
4. Report the PR URL, changed files, and verification.

Determine the default branch from a user/repo instruction or the base remote's
`HEAD`; if that is unclear, ask — don't infer it from a local `main`/`master`
name. With multiple remotes and no clear base, ask which is the base and which
receives the branch rather than assuming `origin`. With no remote or no GitHub
path, do the local branch/commit work and stop, explaining what's missing (a
GitHub auth/network/API error is a failed GitHub operation, not "no remote").

## Merge (only on explicit instruction)

Before merging, require all of:

- The user explicitly told you to merge this PR.
- Local tests pass and every required GitHub check is green (not pending).
- The PR is open, targets the default branch, and its head matches the pushed
  branch and local `HEAD`.
- Unrelated user changes are preserved.

Merge strategy: follow an explicit user/repo instruction or a strategy already
chosen (e.g. configured auto-merge); otherwise **default to a merge commit
(`--merge`)**. Use squash or rebase only when the user or repo indicates it.
Don't silently switch strategy if the chosen one is unavailable — stop and ask.

## Clean up (after a verified merge)

1. Confirm the PR is actually merged (state MERGED) before cleaning up.
2. Switch to the default branch without stashing or discarding unrelated
   changes, and fast-forward it from the base remote.
3. Delete the remote feature branch if the merge didn't already remove it, then
   the local branch. A branch that is already gone is success, not an error. If
   the local branch won't delete because a squash/rebase left its commits
   "unmerged," force-delete only after confirming the PR merged.
4. End on the default branch; run `git status --short --branch` and report the
   PR URL, merge strategy, verification, branch cleanup, and any preserved work.

## Safety

- Never `git reset --hard`, force-push, or delete a branch when unsure which
  branch holds unique work — ask first.
- To undo an accidental, unpushed commit on the default branch: first create a
  feature branch at the current commit, then move the default branch ref back to
  its upstream with `git branch -f <default> <upstream>` (never `git reset
  --hard`), preserving uncommitted work. Then continue only the authorized
  stage and explain the recovery.
