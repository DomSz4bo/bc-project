from typing import Literal

from pydantic import BaseModel, Field

from src.graph.state import AgentState
from src.utils.llm import gemini_flash

SYSTEM_PROMPT = ""


class SupervisorOutput(BaseModel):
    next_step: Literal["DESIGN", "IMPLEMENT", "USER"] = Field(
        description=("The next step. Must be one of DESIGN, IMPLEMENT and USER. "),
    )
    refined_intent: str | None = Field(
        default=None,
        description=(
            "If next step is DESIGN, the summarized goal after any clarifications. "
            "Be detailed, include anything that may help the design team adhere to "
            "the user's requirements. "
            "Else onit this field."
        ),
    )
    message_to_user: str | None = Field(
        description=(
            "If next step is USER, a message aimed at the user. Else omit this field."
        ),
    )


llm_with_structure = gemini_flash.with_structured_output(SupervisorOutput)

async def supervisor(state: AgentState) -> AgentState:
    return state
