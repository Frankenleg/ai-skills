---
name: new-git-project
description: Scaffold a new project AS A GIT REPOSITORY — git init, a minimal .gitignore and .gitattributes, a light canonical AGENTS.md plus a CLAUDE.md that imports it, and an initial commit on main. Use when starting a new project/repo that should be version-controlled, or to add git to a project already scaffolded by new-project. Does NOT create a remote. Use new-project instead if you do NOT want git.
---

# New Git Project Scaffolder

Set up a new project as a git repository with agent instruction files, using the
"AGENTS.md canonical, CLAUDE.md imports it" pattern. This is a **script-driven**
skill: `scaffold.py` does all the deterministic, idempotent work (git init,
ignore/attributes, files, initial commit). Your only judgment is the project
**name** and a one-line **description**. Safe to run on an empty directory, right
after `new-project` (it just adds git), or again on an already-set-up project.

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
   defaults to the current directory. The script is idempotent — it initializes
   git on `main` only if needed, creates each of `.gitignore`,
   `.gitattributes`, `AGENTS.md`, `CLAUDE.md` only if missing (existing files
   kept byte-for-byte), and makes the `Initial project scaffold` commit only if
   the repo has no history. It **never** creates a remote.

3. **Report** what it did — git initialized or already present, which files were
   created vs. kept, whether the initial commit was made, and any defaults used.
   Creating/pushing a remote is a separate, deliberate step for the user.
