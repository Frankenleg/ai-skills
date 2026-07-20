---
name: new-project
description: Scaffold a new project's agent instruction files — a light canonical AGENTS.md plus a CLAUDE.md that imports it. Use when starting a new or empty project/repo that needs baseline agent guidance and you do NOT want a git repository created. Use new-git-project instead if you also want git initialized. Do not use to edit an existing, already-scaffolded instruction set.
---

# New Project Scaffolder (no git)

Set up a new project's agent instruction files using the "AGENTS.md canonical,
CLAUDE.md imports it" pattern, so Codex and Claude Code share one source of
truth. This is a **script-driven** skill: the deterministic file-writing lives
in `scaffold.py`; your only judgment is the project **name** and a one-line
**description**.

## Steps

1. **Decide the name and description.**
   - If the user gave them (conversation or arguments), use those.
   - If you can ask and don't know, ask before running.
   - If running autonomously, omit the flag(s) you don't know — `scaffold.py`
     defaults the name to the current directory's basename and leaves the
     description as a literal placeholder. Report any default that kicked in.

2. **Run the scaffolder** from the project root, passing what you know:

   ```bash
   python scaffold.py --name "<Project Name>" --description "<one-line description>"
   ```

   Omit `--name` and/or `--description` to accept the defaults. `--target`
   defaults to the current directory.

   It writes `AGENTS.md`, `CLAUDE.md`, and a `docs/decisions.md` decision-log
   stub.

3. **Report** the files it created or skipped, and state any defaults used so
   the user can correct them. The script never touches git and never overwrites
   an existing file.
