import asyncio
import locale
import sys
from functools import lru_cache
from pathlib import Path

from langchain.tools import ToolRuntime, tool
from langchain_mcp_adapters.client import MultiServerMCPClient

from src.graph.state import GraphContext


@lru_cache(maxsize=1)
def get_mcp_client():
    return MultiServerMCPClient(
        {
            "filesystem": {
                "transport": "stdio",
                "command": "npx",
                "args": [
                    "-y",
                    "@modelcontextprotocol/server-filesystem",
                    str(Path.cwd()),
                ],
            }
        }
    )


file_tools = asyncio.run(get_mcp_client().get_tools(server_name="filesystem"))


@tool
async def activate_skill(skill_name: str, runtime: ToolRuntime[GraphContext]) -> str:
    """
    Loads full instructions of the skill with the give `skill_name`.
    Use this tool when a task matches a skill's description.
    """
    skill_manager = runtime.context.get("skill_manager", None)

    if skill_manager is None or not skill_manager.has_skill(skill_name):
        return (
            "There was an issue accessing the skill. "
            f"Make sure '{skill_name}' is a valid skill name listed in your skill catalog."
        )

    skill = skill_manager.get_skill(skill_name)

    skill_content = f"""<skill_content name="{skill["name"]}">
{skill["body"]}

Skill directory: {skill["location"].parent}
Relative paths in this skill are relative to the skill directory.
</skill_content>
"""

    return skill_content


@tool
async def run_tests(runtime: ToolRuntime[GraphContext]) -> str:
    """
    Executes the pytest suite. Returns the output of the test run.
    Use this to verify your changes.
    """
    args = ["-m", "pytest", "-q", "--tb=short"]
    output, returncode = await _run_async_subprocess_with_output(
        sys.executable, *args, cwd=runtime.context["working_directory"]
    )

    if returncode == 0:
        return f"✅ Tests Passed\n{output}"
    else:
        return f"❌ Tests Failed (Code {returncode}):\n{output}"


@tool
async def run_tests_with_coverage(runtime: ToolRuntime[GraphContext]) -> str:
    """
    Executes the pytest suite with coverage. Returns the test output and code coverage percentages.
    Use this tool to evaluate tests and test coverage.
    """
    args = ["-m", "pytest", "--cov=src", "--cov=term-missing", "-q", "--tb=short"]
    output, returncode = await _run_async_subprocess_with_output(
        sys.executable, *args, cwd=runtime.context["working_directory"]
    )

    if returncode == 0:
        return f"✅ Tests Passed\n{output}"
    else:
        return f"❌ Tests Failed (Code {returncode}):\n{output}"


async def _run_async_subprocess_with_output(program, *args, cwd=None):
    process = await asyncio.create_subprocess_exec(
        program,
        *args,
        cwd=cwd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )

    stdout, stderr = await process.communicate()
    encoding = locale.getpreferredencoding()
    result_text = stdout.decode(encoding, errors="replace") + stderr.decode(
        encoding, errors="replace"
    )

    return result_text, process.returncode
