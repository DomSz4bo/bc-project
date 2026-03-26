import asyncio
import locale
import sys

from langchain.tools import ToolRuntime, tool

from src.graph.state import GraphContext


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
