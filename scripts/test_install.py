import importlib.util
from pathlib import Path

_spec = importlib.util.spec_from_file_location(
    "install_mod", Path(__file__).parent / "install.py"
)
inst = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(inst)


def test_install_copies_runtime_files_not_tests(tmp_path):
    skills = tmp_path / "skills"
    (skills / "demo").mkdir(parents=True)
    (skills / "demo" / "SKILL.md").write_text("s", encoding="utf-8")
    (skills / "demo" / "scaffold.py").write_text("c", encoding="utf-8")
    (skills / "demo" / "test_scaffold.py").write_text("t", encoding="utf-8")
    claude = tmp_path / "claude"
    agents = tmp_path / "agents"
    report = inst.install(skills, [claude, agents])
    for root in (claude, agents):
        assert (root / "demo" / "SKILL.md").read_text(encoding="utf-8") == "s"
        assert (root / "demo" / "scaffold.py").read_text(encoding="utf-8") == "c"
        assert not (root / "demo" / "test_scaffold.py").exists()
    assert len(report["copied"]) == 4  # 2 files x 2 dests


def test_discover_skills_requires_skill_md(tmp_path):
    skills = tmp_path / "skills"
    (skills / "real").mkdir(parents=True)
    (skills / "real" / "SKILL.md").write_text("x", encoding="utf-8")
    (skills / "notaskill").mkdir(parents=True)  # no SKILL.md
    found = [p.name for p in inst.discover_skills(skills)]
    assert found == ["real"]


def _make_skill(skills_root, name):
    d = skills_root / name
    d.mkdir(parents=True)
    (d / "SKILL.md").write_text(name, encoding="utf-8")
    (d / "scaffold.py").write_text(name, encoding="utf-8")


def test_install_selected_skill_only(tmp_path):
    skills = tmp_path / "skills"
    _make_skill(skills, "alpha")
    _make_skill(skills, "beta")
    dest = tmp_path / "claude"
    inst.install(skills, [dest], names=["beta"])
    assert (dest / "beta" / "SKILL.md").exists()
    assert not (dest / "alpha").exists()


def test_install_all_when_no_names(tmp_path):
    skills = tmp_path / "skills"
    _make_skill(skills, "alpha")
    _make_skill(skills, "beta")
    dest = tmp_path / "claude"
    inst.install(skills, [dest])  # names omitted -> all
    assert (dest / "alpha" / "SKILL.md").exists()
    assert (dest / "beta" / "SKILL.md").exists()


def test_install_unknown_skill_raises(tmp_path):
    skills = tmp_path / "skills"
    _make_skill(skills, "alpha")
    dest = tmp_path / "claude"
    try:
        inst.install(skills, [dest], names=["nope"])
    except ValueError as e:
        assert "nope" in str(e)
        assert "alpha" in str(e)  # lists what is available
    else:
        raise AssertionError("expected ValueError for unknown skill")
    assert not (dest / "alpha").exists()  # nothing installed on error


def test_default_codex_dir_honors_codex_home(monkeypatch, tmp_path):
    monkeypatch.setenv("CODEX_HOME", str(tmp_path / "cx"))
    assert inst.default_codex_dir() == tmp_path / "cx" / "skills"


def test_default_codex_dir_falls_back_to_dot_codex(monkeypatch, tmp_path):
    monkeypatch.delenv("CODEX_HOME", raising=False)
    monkeypatch.setattr(inst.Path, "home", staticmethod(lambda: tmp_path))
    # Codex discovers skills under ~/.codex/skills, NOT ~/.agents/skills.
    assert inst.default_codex_dir() == tmp_path / ".codex" / "skills"
    assert inst.default_codex_dir() != tmp_path / ".agents" / "skills"


def test_default_claude_dir(monkeypatch, tmp_path):
    monkeypatch.setattr(inst.Path, "home", staticmethod(lambda: tmp_path))
    assert inst.default_claude_dir() == tmp_path / ".claude" / "skills"


def test_install_copies_subdirectories(tmp_path):
    skills = tmp_path / "skills"
    (skills / "prose" / "agents").mkdir(parents=True)
    (skills / "prose" / "SKILL.md").write_text("s", encoding="utf-8")
    (skills / "prose" / "agents" / "openai.yaml").write_text("y", encoding="utf-8")
    dest = tmp_path / "claude"
    report = inst.install(skills, [dest])
    assert (dest / "prose" / "SKILL.md").read_text(encoding="utf-8") == "s"
    assert (dest / "prose" / "agents" / "openai.yaml").read_text(encoding="utf-8") == "y"
    assert len(report["copied"]) == 2  # SKILL.md + agents/openai.yaml


def test_runtime_files_excludes_tests_and_caches(tmp_path):
    skill = tmp_path / "s"
    (skill / "__pycache__").mkdir(parents=True)
    (skill / "SKILL.md").write_text("s", encoding="utf-8")
    (skill / "scaffold.py").write_text("c", encoding="utf-8")
    (skill / "test_scaffold.py").write_text("t", encoding="utf-8")
    (skill / "__pycache__" / "scaffold.cpython-312.pyc").write_text("x", encoding="utf-8")
    names = {p.as_posix() for p in inst.runtime_files(skill)}
    assert names == {"SKILL.md", "scaffold.py"}


def test_check_reports_missing_then_current_then_stale(tmp_path):
    skills = tmp_path / "skills"
    _make_skill(skills, "alpha")
    dest = tmp_path / "claude"

    r1 = inst.check(skills, [dest])
    assert r1["skills"]["alpha"][str(dest)]["status"] == "missing"
    assert r1["drift"] is True

    inst.install(skills, [dest])
    r2 = inst.check(skills, [dest])
    assert r2["skills"]["alpha"][str(dest)]["status"] == "current"
    assert r2["drift"] is False

    (dest / "alpha" / "SKILL.md").write_text("mutated", encoding="utf-8")
    r3 = inst.check(skills, [dest])
    assert r3["skills"]["alpha"][str(dest)]["status"] == "stale"
    assert r3["drift"] is True


def test_check_cli_exit_codes(tmp_path, capsys):
    skills = tmp_path / "skills"
    _make_skill(skills, "alpha")
    dest = tmp_path / "claude"
    argv_check = ["--check", "--skills-root", str(skills),
                  "--claude-dir", str(dest), "--codex-dir", str(tmp_path / "x")]
    assert inst.main(argv_check) == 1          # missing -> drift -> exit 1
    inst.main(["--skills-root", str(skills),
               "--claude-dir", str(dest), "--codex-dir", str(tmp_path / "x")])
    assert inst.main(argv_check) == 0          # now installed -> exit 0


def test_classify_missing_beats_stale_regardless_of_order(tmp_path):
    skills = tmp_path / "skills"
    d = skills / "alpha"
    (d / "agents").mkdir(parents=True)
    (d / "SKILL.md").write_text("s", encoding="utf-8")
    (d / "agents" / "z.yaml").write_text("y", encoding="utf-8")
    dest = tmp_path / "claude"
    inst.install(skills, [dest])
    # one installed file differs (stale), another is gone entirely (missing)
    (dest / "alpha" / "agents" / "z.yaml").write_text("MUTATED", encoding="utf-8")
    (dest / "alpha" / "SKILL.md").unlink()
    rep = inst.check(skills, [dest])
    assert rep["skills"]["alpha"][str(dest)]["status"] == "missing"


def test_check_unknown_skill_raises(tmp_path):
    skills = tmp_path / "skills"
    _make_skill(skills, "alpha")
    try:
        inst.check(skills, [tmp_path / "d"], names=["nope"])
    except ValueError as e:
        assert "nope" in str(e) and "alpha" in str(e)
    else:
        raise AssertionError("expected ValueError")


import json


def test_install_writes_receipt_with_commit_and_per_skill_hash(tmp_path):
    skills = tmp_path / "skills"
    _make_skill(skills, "alpha")
    _make_skill(skills, "beta")
    dest = tmp_path / "claude"
    inst.install(skills, [dest], commit="deadbeef", installed_at="2026-07-19T00:00:00Z")
    receipt = json.loads((dest / ".ai-skills-install.json").read_text(encoding="utf-8"))
    assert receipt["commit"] == "deadbeef"
    assert receipt["installedAt"] == "2026-07-19T00:00:00Z"
    assert set(receipt["skills"]) == {"alpha", "beta"}
    assert len(receipt["skills"]["alpha"]["hash"]) == 64  # sha256 hex


def test_receipt_hash_is_per_skill_independent(tmp_path):
    skills = tmp_path / "skills"
    _make_skill(skills, "alpha")
    _make_skill(skills, "beta")
    dest = tmp_path / "claude"
    inst.install(skills, [dest])
    r1 = json.loads((dest / ".ai-skills-install.json").read_text(encoding="utf-8"))
    # change ONLY beta, reinstall, and confirm alpha's recorded hash is unchanged
    (skills / "beta" / "SKILL.md").write_text("beta CHANGED", encoding="utf-8")
    inst.install(skills, [dest])
    r2 = json.loads((dest / ".ai-skills-install.json").read_text(encoding="utf-8"))
    assert r2["skills"]["alpha"]["hash"] == r1["skills"]["alpha"]["hash"]
    assert r2["skills"]["beta"]["hash"] != r1["skills"]["beta"]["hash"]


def test_install_partial_merges_receipt(tmp_path):
    skills = tmp_path / "skills"
    _make_skill(skills, "alpha")
    _make_skill(skills, "beta")
    dest = tmp_path / "claude"
    inst.install(skills, [dest], names=["alpha"])
    inst.install(skills, [dest], names=["beta"])
    receipt = json.loads((dest / ".ai-skills-install.json").read_text(encoding="utf-8"))
    assert set(receipt["skills"]) == {"alpha", "beta"}  # beta run kept alpha


def test_source_commit_none_when_not_git(tmp_path):
    assert inst.source_commit(tmp_path) is None


def test_check_surfaces_recorded_hash(tmp_path):
    skills = tmp_path / "skills"
    _make_skill(skills, "alpha")
    dest = tmp_path / "claude"
    inst.install(skills, [dest])
    rep = inst.check(skills, [dest])
    entry = rep["skills"]["alpha"][str(dest)]
    assert entry["recordedHash"] == entry["currentHash"]
    assert entry["recordedHash"] is not None
