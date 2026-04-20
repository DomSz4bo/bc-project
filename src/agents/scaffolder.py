from pathlib import Path

from langchain_core.messages import HumanMessage, SystemMessage
from langgraph.config import get_stream_writer
from langgraph.runtime import Runtime
from loguru import logger
from pydantic import BaseModel, Field

from src.graph.state import AgentState, GraphContext
from src.utils.llm import build_fallback_chain, gemini_3p1_flash_lite, gemma_4_31b
from src.utils.streaming import CustomStreamData


class Component(BaseModel):
    class_name: str = Field(
        description="The PascalCase name of the class (e.g., PaymentProcessor)"
    )
    file_name: str = Field(
        description="The snake_case name of the file without extension (e.g., payment_processor)"
    )

    def __str__(self):
        return f"{self.file_name} -> {self.class_name}"


class ScaffoldPlan(BaseModel):
    analysis: str = Field(
        description="Analyze ALL participants in the diagram before creating components."
    )
    components: list[Component] = Field(
        description="List of internal system components to scaffold"
    )

    def __str__(self):
        return "\n".join(str(comp) for comp in self.components)


structured_llm = build_fallback_chain(
    gemini_3p1_flash_lite, gemma_4_31b, schema=ScaffoldPlan
)


async def scaffolder(state: AgentState, runtime: Runtime[GraphContext]) -> AgentState:
    """
    The Scaffolder node logic.
    Translates the Sequence Diagram and Use Case into a project scaffold.
    """
    writer = get_stream_writer()
    writer(
        CustomStreamData(
            "Creating project structure", "start", {"spinner": "growVertical"}
        )
    )
    logger.info("Scaffolder node initiated.")

    use_case = state.get("use_case")
    sequence_diagram = state.get("sequence_diagram")
    working_dir = runtime.context.get("working_directory")

    if not use_case or not sequence_diagram:
        raise ValueError("Missing use_case or sequence_diagram in AgentState.")
    if not working_dir:
        raise ValueError("Missing working_directory in GraphContext.")

    src_dir = working_dir / "src"

    messages = [
        SystemMessage(SYSTEM_PROMPT),
        HumanMessage(
            HUMAN_PROMPT.format(use_case=use_case, sequence_diagram=sequence_diagram)
        ),
    ]

    plan: ScaffoldPlan = await structured_llm.ainvoke(messages)
    logger.debug(f"Scaffolder plan:\n{plan}")

    write_scaffold_to_disk(plan, src_dir)

    writer(CustomStreamData("Project structure created.", "end"))
    logger.info("Scaffold written to disk.")

    return {}


def write_scaffold_to_disk(plan: ScaffoldPlan, src_dir: Path) -> None:
    src_dir.mkdir(parents=True, exist_ok=True)
    (src_dir / "__init__.py").touch(exist_ok=True)

    for component in plan.components:
        file_path = src_dir / f"{component.file_name}.py"

        content = f"class {component.class_name}:\n    pass\n"

        logger.info(f"Scaffolding {file_path}")
        with open(file_path, "w") as f:
            f.write(content)


SYSTEM_PROMPT = """
You are the Interface Scaffolder Agent in a Python development pipeline. 
Your task is to analyze a Use Case and a Mermaid Sequence Diagram to identify the system and its components that need to be built.

<rules>
1. **Analyze Every Participant**: Look at all `participants` in the Sequence Diagram.
2. **Filter Externals**: Do NOT scaffold Primary Actors (e.g., User, Admin) or External Dependencies (e.g., StripeAPI, ExternalDatabase) defined in the Use Case.
3. **Identify Internals**: Scaffold only the core components of the system being built.
4. **Naming Conventions**: Classes must be PascalCase. Files must be snake_case.
5. **Chain of Thought**: You MUST analyze each participant first in the `analysis` array before generating the final `components` list.
</rules>
"""

HUMAN_PROMPT = """
<use_case>
{use_case}
</use_case>

<sequence_diagram>
{sequence_diagram}
</sequence_diagram>
"""
