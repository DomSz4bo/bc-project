from pathlib import Path

from langchain_core.messages import HumanMessage, SystemMessage
from langgraph.runtime import Runtime
from loguru import logger
from pydantic import BaseModel, Field

from src.graph.state import AgentState, GraphContext
from src.utils.llm import gemini_3p1_flash_lite as llm


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
    components: list[Component] = Field(
        description="List of internal system components to scaffold"
    )

    def __str__(self):
        return "\n".join(str(comp) for comp in self.components)


structured_llm = llm.with_structured_output(ScaffoldPlan)


async def scaffolder(state: AgentState, runtime: Runtime[GraphContext]) -> AgentState:
    """
    The Scaffolder node logic.
    Translates the Sequence Diagram and Use Case into a project scaffold.
    """
    logger.debug("Scaffolder node initiated.")

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
    logger.debug("Scaffold written to disk.")

    return state


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
You are the Scaffolder Agent in a software development pipeline. Your task is to identify the **Internal System Components** that need to be implemented based on a Use Case and a Sequence Diagram.

---

## INPUTS
1. **Use Case**: Defines Primary Actors and Secondary Actors (External Dependencies/Mocks).
2. **Sequence Diagram**: A Mermaid sequence diagram shows interactions between Actors and Participants.

---

## RULES
1. **Identify Internal Components**: Look at the `participants` in the Sequence Diagram.
2. **Exclude External Actors**: Do NOT scaffold Primary Actors that aren't part of the system (e.g., Customer, User) or Secondary Actors explicitly labeled as "Mock", "External", or "Dependency" in the Use Case.
3. **Focus on the "System"**: If a participant represents the system being built or its internal modules, it must be scaffolded.
4. **Naming Conventions**:
   - `class_name`: PascalCase (e.g., VendingMachine).
   - `file_name`: snake_case (e.g., vending_machine).

---

## OUTPUT
Return a structured list of components, each with a `class_name` and `file_name`.
"""

HUMAN_PROMPT = """
**Use Case**:
{use_case}

**Sequence Diagram**:
{sequence_diagram}
"""
