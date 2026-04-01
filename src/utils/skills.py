from pathlib import Path
from typing import Any, Sequence, TypedDict

import yaml


class SkillInfo(TypedDict):
    name: str
    description: str
    location: Path
    body: str


SKILL_MD = "SKILL.md"
PARSING_WARNING = "Failed to parse skill: '{file_path}'."
NAME_WARNING = (
    "Skills with duplicate names: '{skill_name}'. Only one will be available."
)


class SkillManager:
    """Manages the reading and retrieval of Agent Skills."""

    def __init__(self, root_dirs: Sequence[Path]):
        """
        Create a new `SkillManager` with an empty registry.
        Use `reload_skills` to search and load skills from the specified directories.
        Args:
            root_dirs: List of directories to search for skills.
                A root directory should contain a `.agents/skills/` sub-directory with skill
                definitions that follow the Agent Skills [specification](https://agentskills.io/specification).
        """
        self._registry: dict[str, SkillInfo] = {}
        self._dirs_to_search = root_dirs
        self._warnings: list[str] = []
        self._is_cataloged: bool = False
        self._cached_catalog: str = ""

    def has_available_skills(self) -> bool:
        return bool(self._registry)

    def has_skill(self, skill_name: str) -> bool:
        "Returns whether there is a skill registered with the given `skill_name`."
        return skill_name in self._registry

    def get_skill(self, skill_name: str) -> SkillInfo:
        """
        Returns the `SkillInfo` associated with the given `skill_name`.
        Raises `KeyError` if there is no skill registered under `skill_name`.
        """
        return self._registry[skill_name]

    def get_skill_catalog(self) -> str:
        "Returns a structured catalog of skills available. Includes skill names and descriptions."
        if not self._is_cataloged:
            self._cached_catalog = self._build_skill_catalog()
            self._is_cataloged = True

        return self._cached_catalog

    def reload_skills(self) -> None:
        """
        Searches the root directories given in the constructor for `.agents/skills/` sub-directories
        and parses the skill definitions. The previous registry contents are cleared and overwritten.
        """
        self._reset_state()
        skill_files: list[Path] = []

        for dir in self._dirs_to_search:
            skill_files += self._find_skill_files(dir)

        for file in skill_files:
            try:
                skill_info = self._parse_skill_md(file)
            except SkillParsingError as e:
                self._add_parsing_warning(file, e.message)
                continue
            except Exception as e:
                msg = getattr(e, "message", str(e))
                error_msg = f"Unexpected {type(e)}" + (f": {msg}" if msg else "")
                self._add_parsing_warning(file, error_msg)
                continue

            if skill_info["name"] in self._registry:
                self._add_name_conflict_warning(skill_info["name"])
                continue

            self._registry[skill_info["name"]] = skill_info

    def _reset_state(self):
        self._registry.clear()
        self._warnings.clear()
        self._is_cataloged = False
        self._cached_catalog = ""

    def _add_parsing_warning(self, for_file: Path, error_msg: str = None) -> None:
        warning = PARSING_WARNING.format(
            file_path=get_relative_path_with_fallback(for_file)
        )
        if error_msg:
            warning += f"\n  - {error_msg}"
        self._warnings.append(warning)

    def _add_name_conflict_warning(self, for_name: str) -> None:
        self._warnings.append(NAME_WARNING.format(skill_name=for_name))

    def get_warnings(self):
        return self._warnings

    def _find_skill_files(self, root_dir: Path) -> list[Path]:
        skills_dir = root_dir / ".agents" / "skills"

        if not skills_dir.is_dir():
            return []

        skill_files = []

        for path in sorted(skills_dir.iterdir()):
            skill_file_path = path / SKILL_MD
            if skill_file_path.is_file():
                skill_files.append(skill_file_path)

        return skill_files

    def _parse_skill_md(self, file_path: Path) -> SkillInfo:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()

        if not content.startswith("---"):
            raise SkillParsingError(
                "Incorrect frontmatter format. Must start with '---'!"
            )

        parts = content.split("---", 2)
        if len(parts) != 3:
            raise SkillParsingError(
                "Incorrect frontmatter format. Must end with '---'!"
            )

        _, frontmatter, markdown_content = parts
        markdown_content = markdown_content.strip()

        try:
            skill_metadata: dict[str, Any] = yaml.safe_load(frontmatter)
        except yaml.YAMLError as e:
            raise SkillParsingError(f"Invalid YAML in frontmatter: {e}")

        if not isinstance(skill_metadata, dict):
            raise SkillParsingError("Frontmatter must be a YAML dictionary.")

        name = skill_metadata.get("name")
        if not name or not isinstance(name, str):
            raise SkillParsingError("Missing or incorrect 'name' format.")

        description = skill_metadata.get("description")
        if not description or not isinstance(description, str):
            raise SkillParsingError("Missing or incorrect 'description' format.")

        return SkillInfo(
            name=name,
            description=description,
            location=file_path.absolute(),
            body=markdown_content,
        )

    SKILL_BLOCK = """  <skill>
    <name>{name}</name>
    <description>{description}</description>
  </skill>
"""

    def _build_skill_catalog(self) -> str:
        if not self._registry:
            return ""

        catalog = "<available_skills>\n"

        for skill in self._registry.values():
            catalog += self.SKILL_BLOCK.format(
                name=skill["name"],
                description=skill["description"],
            )

        catalog += "</available_skills>"
        return catalog


def get_relative_path_with_fallback(filepath: Path):
    """
    Returns the relative path from the current working directory.
    Falls back to relative path from user's home directory prepended with "~/".
    If that also fails, returns the unchanged path.
    """
    try:
        return filepath.relative_to(Path.cwd())
    except ValueError:
        pass
    try:
        return "~" / filepath.relative_to(Path.home())
    except ValueError:
        pass
    return filepath


class SkillParsingError(Exception):
    def __init__(self, message: str):
        self.message = message
        super().__init__(message)
