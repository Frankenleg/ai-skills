import re
from pathlib import Path

SKILL_DIR = Path(__file__).resolve().parent


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
    fm = _frontmatter((SKILL_DIR / "SKILL.md").read_text(encoding="utf-8"))
    assert fm["name"] == "github-flow"
    assert len(fm["description"]) > 0


def test_is_prose_skill_no_scaffold():
    # github-flow is prose by design: no scaffold.py.
    assert not (SKILL_DIR / "scaffold.py").exists()


def test_agents_metadata_present():
    assert (SKILL_DIR / "agents" / "openai.yaml").exists()
