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
