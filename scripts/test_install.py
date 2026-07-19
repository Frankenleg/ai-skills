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
