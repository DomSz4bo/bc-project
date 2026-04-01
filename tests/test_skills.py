from pathlib import Path

import pytest

from src.utils.skills import SkillManager


def create_skill_file(path: Path, name: str, description: str, body: str):
    content = f"---\nname: {name}\ndescription: {description}\n---\n{body}"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


class TestSkillManager:
    def test_init(self, tmp_path):
        manager = SkillManager([tmp_path])
        assert not manager.has_available_skills()
        assert manager.get_warnings() == []

    def test_find_skills(self, tmp_path):
        root = tmp_path / "root"
        skill_path = root / ".agents" / "skills" / "skill1" / "SKILL.md"
        create_skill_file(
            skill_path, "test-skill", "A test skill", "Skill body content"
        )

        manager = SkillManager([root])
        manager.reload_skills()

        assert manager.has_available_skills()
        assert manager.has_skill("test-skill")

        skill = manager.get_skill("test-skill")
        assert skill["name"] == "test-skill"
        assert skill["description"] == "A test skill"
        assert skill["body"] == "Skill body content"
        assert skill["location"] == skill_path.absolute()
        assert manager.get_warnings() == []

    def test_get_skill_error(self, tmp_path):
        manager = SkillManager([tmp_path])
        manager.reload_skills()
        with pytest.raises(KeyError):
            manager.get_skill("non-existent")

    def test_no_skills_dir(self, tmp_path):
        root = tmp_path / "root"
        root.mkdir()

        manager = SkillManager([root])
        manager.reload_skills()

        assert not manager.has_available_skills()
        assert manager.get_warnings() == []

    def test_duplicate_names(self, tmp_path):
        root1 = tmp_path / "root1"
        root2 = tmp_path / "root2"

        create_skill_file(
            root1 / ".agents" / "skills" / "s1" / "SKILL.md",
            "duplicate",
            "desc1",
            "body1",
        )
        create_skill_file(
            root2 / ".agents" / "skills" / "s2" / "SKILL.md",
            "duplicate",
            "desc2",
            "body2",
        )

        manager = SkillManager([root1, root2])
        manager.reload_skills()

        assert manager.has_skill("duplicate")
        assert len(manager.get_warnings()) == 1
        assert "duplicate" in manager.get_warnings()[0]

    def test_parsing_errors(self, tmp_path):
        root = tmp_path / "root"
        skills_dir = root / ".agents" / "skills"

        # 1. Missing start ---
        (skills_dir / "err1").mkdir(parents=True)
        (skills_dir / "err1" / "SKILL.md").write_text(
            "no frontmatter", encoding="utf-8"
        )

        # 2. Missing end ---
        (skills_dir / "err2").mkdir(parents=True)
        (skills_dir / "err2" / "SKILL.md").write_text(
            "---\nname: test", encoding="utf-8"
        )

        # 3. Missing name
        (skills_dir / "err3").mkdir(parents=True)
        (skills_dir / "err3" / "SKILL.md").write_text(
            "---\ndescription: desc\n---\nbody", encoding="utf-8"
        )

        (skills_dir / "err4").mkdir(parents=True)
        (skills_dir / "err4" / "SKILL.md").write_text(
            "---\nname: : invalid\n---\nbody", encoding="utf-8"
        )

        (skills_dir / "err5").mkdir(parents=True)
        (skills_dir / "err5" / "SKILL.md").write_text(
            "---\njust a string\n---\nbody", encoding="utf-8"
        )

        manager = SkillManager([root])
        manager.reload_skills()

        assert not manager.has_available_skills()
        assert len(manager.get_warnings()) == 5

        warnings = manager.get_warnings()
        assert any("Incorrect frontmatter format" in w for w in warnings)
        assert any("Missing or incorrect 'name' field" in w for w in warnings)
        assert any("Invalid YAML in frontmatter" in w for w in warnings)
        assert any("Frontmatter must be a YAML dictionary" in w for w in warnings)

    def test_catalog(self, tmp_path):
        root = tmp_path / "root"
        create_skill_file(
            root / ".agents" / "skills" / "s1" / "SKILL.md", "skill1", "desc1", "body1"
        )
        create_skill_file(
            root / ".agents" / "skills" / "s2" / "SKILL.md", "skill2", "desc2", "body2"
        )

        manager = SkillManager([root])

        assert manager.get_skill_catalog() == ""

        manager.reload_skills()
        catalog = manager.get_skill_catalog()

        assert "<available_skills>" in catalog
        assert "<name>skill1</name>" in catalog
        assert "<description>desc1</description>" in catalog
        assert "<name>skill2</name>" in catalog
        assert "<description>desc2</description>" in catalog
        assert "</available_skills>" in catalog

        assert manager.get_skill_catalog() == catalog

    def test_reload_resets_state(self, tmp_path):
        root = tmp_path / "root"
        skill_path = root / ".agents" / "skills" / "s1" / "SKILL.md"
        create_skill_file(skill_path, "skill1", "desc1", "body1")

        manager = SkillManager([root])
        manager.reload_skills()
        assert manager.has_skill("skill1")
        assert "skill1" in manager.get_skill_catalog()

        skill_path.unlink()
        manager.reload_skills()

        assert not manager.has_skill("skill1")
        assert manager.get_skill_catalog() == ""
        assert not manager.has_available_skills()
