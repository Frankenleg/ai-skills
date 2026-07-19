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
