from pathlib import Path

from src.utils.skills import SkillManager


def create_skill_file(path: Path, name: str, description: str, body: str):
    content = f"---\nname: {name}\ndescription: {description}\n---\n{body}"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def test_skill_manager_init(tmp_path):
    manager = SkillManager([tmp_path])
    assert manager.get_skills_registry() == {}
    assert manager.get_warnings() == []


def test_skill_manager_find_skills(tmp_path):
    # Setup: root/.agents/skills/skill1/SKILL.md
    root = tmp_path / "root"
    skill_path = root / ".agents" / "skills" / "skill1" / "SKILL.md"
    create_skill_file(skill_path, "test-skill", "A test skill", "Skill body content")

    manager = SkillManager([root])
    manager.reload_skills()

    registry = manager.get_skills_registry()
    assert "test-skill" in registry
    assert registry["test-skill"]["name"] == "test-skill"
    assert registry["test-skill"]["description"] == "A test skill"
    assert registry["test-skill"]["body"] == "Skill body content"
    assert registry["test-skill"]["location"] == skill_path.absolute()
    assert manager.get_warnings() == []


def test_skill_manager_no_skills_dir(tmp_path):
    root = tmp_path / "root"
    root.mkdir()

    manager = SkillManager([root])
    manager.reload_skills()

    assert manager.get_skills_registry() == {}
    assert manager.get_warnings() == []


def test_skill_manager_duplicate_names(tmp_path):
    root1 = tmp_path / "root1"
    root2 = tmp_path / "root2"

    create_skill_file(
        root1 / ".agents" / "skills" / "s1" / "SKILL.md", "duplicate", "desc1", "body1"
    )
    create_skill_file(
        root2 / ".agents" / "skills" / "s2" / "SKILL.md", "duplicate", "desc2", "body2"
    )

    manager = SkillManager([root1, root2])
    manager.reload_skills()

    assert len(manager.get_skills_registry()) == 1
    assert "duplicate" in manager.get_skills_registry()
    assert len(manager.get_warnings()) == 1
    assert "duplicate" in manager.get_warnings()[0]


def test_skill_manager_parsing_errors(tmp_path):
    root = tmp_path / "root"
    skills_dir = root / ".agents" / "skills"

    # 1. Missing start ---
    (skills_dir / "err1").mkdir(parents=True)
    (skills_dir / "err1" / "SKILL.md").write_text("no frontmatter", encoding="utf-8")

    # 2. Missing end ---
    (skills_dir / "err2").mkdir(parents=True)
    (skills_dir / "err2" / "SKILL.md").write_text("---\nname: test", encoding="utf-8")

    # 3. Missing name
    (skills_dir / "err3").mkdir(parents=True)
    (skills_dir / "err3" / "SKILL.md").write_text(
        "---\ndescription: desc\n---\nbody", encoding="utf-8"
    )

    # 4. Invalid YAML (ScannerError)
    (skills_dir / "err4").mkdir(parents=True)
    (skills_dir / "err4" / "SKILL.md").write_text(
        "---\nname: : invalid\n---\nbody", encoding="utf-8"
    )

    # 5. Frontmatter not a dict (e.g. just a string)
    (skills_dir / "err5").mkdir(parents=True)
    (skills_dir / "err5" / "SKILL.md").write_text(
        "---\njust a string\n---\nbody", encoding="utf-8"
    )

    manager = SkillManager([root])
    manager.reload_skills()

    assert manager.get_skills_registry() == {}
    assert len(manager.get_warnings()) == 5

    warnings = manager.get_warnings()
    assert any("Incorrect frontmatter format" in w for w in warnings)
    assert any("Missing or incorrect 'name' format" in w for w in warnings)
    assert any("Invalid YAML in frontmatter" in w for w in warnings)
    assert any("Frontmatter must be a YAML dictionary" in w for w in warnings)
