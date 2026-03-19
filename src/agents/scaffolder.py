from typing import List

from langgraph.runtime import Runtime
from loguru import logger
from pydantic import BaseModel, Field

from src.graph.state import AgentState, GraphContext
from src.utils.llm import gemini_3_flash as llm


class Component(BaseModel):
    class_name: str = Field(
        description="The PascalCase name of the class (e.g., VendingMachine)"
    )
    file_name: str = Field(
        description="The snake_case name of the file without extension (e.g., vending_machine)"
    )


class ScaffoldPlan(BaseModel):
    components: List[Component] = Field(
        description="List of internal system components to scaffold"
    )


# Bind the structured output at the module level
structured_llm = llm.with_structured_output(ScaffoldPlan)


async def scaffolder(state: AgentState, runtime: Runtime[GraphContext]) -> AgentState:
    """
    The Scaffolder node logic.
    Translates the Sequence Diagram and Use Case into a project scaffold.
    """
    logger.debug("Scaffolder node initiated.")

    use_case = state.get("use_case", None)
    sequence_diagram = state.get("sequence_diagram", None)
    working_dir = runtime.context.get("working_directory", None)

    if not use_case or not sequence_diagram:
        raise ValueError("Missing use_case or sequence_diagram in AgentState.")
    if not working_dir:
        raise ValueError("Missing working_directory in GraphContext.")

    src_dir = working_dir / "src"

    prompt = SYSTEM_PROMPT.format(use_case=use_case, sequence_diagram=sequence_diagram)

    plan: ScaffoldPlan = await structured_llm.ainvoke(prompt)
    logger.debug(f"Scaffolder plan: {plan}")

    src_dir.mkdir(parents=True, exist_ok=True)
    (src_dir / "__init__.py").touch(exist_ok=True)

    for component in plan.components:
        file_path = src_dir / f"{component.file_name}.py"

        content = f"class {component.class_name}:\n    pass\n"

        logger.info(f"Scaffolding {file_path}")
        with open(file_path, "w") as f:
            f.write(content)

    return state


SYSTEM_PROMPT = """
You are the Scaffolder Agent in a software development pipeline. Your task is to identify the **Internal System Components** that need to be implemented based on a Use Case and a Sequence Diagram.

---

## INPUTS
1. **Use Case**: Defines Primary Actors and Secondary Actors (External Dependencies/Mocks).
2. **Sequence Diagram**: Shows interactions between Actors and Participants.

---

## RULES
1. **Identify Internal Components**: Look at the `participants` in the Sequence Diagram.
2. **Exclude External Actors**: Do NOT scaffold Primary Actors (e.g., Customer, User) or Secondary Actors explicitly labeled as "Mock", "External", or "Dependency" in the Use Case.
3. **Focus on the "System"**: If a participant represents the system being built or its internal modules, it must be scaffolded.
4. **Naming Conventions**:
   - `class_name`: PascalCase (e.g., VendingMachine).
   - `file_name`: snake_case (e.g., vending_machine).

---

## OUTPUT
Return a structured list of components, each with a `class_name` and `file_name`.

---

## CONTEXT
**Use Case**:
{use_case}

**Sequence Diagram**:
{sequence_diagram}
"""
