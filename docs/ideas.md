# Skill ideas (backlog)

Future skills to consider — captured, not yet designed or committed to.

## new-private-repo (or a `--private` option)

A variant that scaffolds a project **and sets up a private remote** — e.g.
create a private GitHub repo, push, and optionally wire safeguards. Distinct from
`new-git-project`, which deliberately stays local (no remote).

Things to work through if we design it:

- **Creating/pushing a remote is an outward-facing action** — confirm before
  doing it; don't do it silently.
- **Private-repo branch protection needs a paid plan** (GitHub Pro/Team) — a
  private-repo skill can't assume protection is available (learned while setting
  up `ai-maintenance`). Decide what to do when it isn't (skip + warn, or make
  public, or leave to the user).
- **Host/auth** — GitHub via `gh`, or host-aware (GitLab, etc.)? Keep it simple
  (gh-only) unless there's a real need.
- **Safeguards** — private repos still benefit from the gitleaks hook and the
  "keep it clean" guardrail; reuse the same pieces.
