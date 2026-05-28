from typing import Any

from dotenv import load_dotenv
from langchain.chat_models import init_chat_model
from langchain.tools import BaseTool
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import AIMessage
from langchain_core.runnables import RunnableLambda, RunnableSerializable
from loguru import logger

load_dotenv()


def build_fallback_chain(
    primary: BaseChatModel,
    *fallbacks: BaseChatModel,
    tools: list[BaseTool] | None = None,
    schema: dict[str, Any] | type | None = None,
) -> RunnableSerializable[Any, AIMessage]:
    """
    Builds a fallback chain of models with logging in between.
    If a model fails, the next one in the list is tried.
    The error that triggered the fallback is logged for debugging.

    Args:
        primary: The first model that will be tried.
        fallbacks: Fallback models in order.
        tools: Optional list of tools to bind to all models.
        schema: Optional Pydantic model or JSON schema for structured output.
    """
    if not fallbacks:
        raise ValueError(
            "At least one fallback must be provided to create a fallback chain."
        )

    if tools is not None and schema is not None:
        raise ValueError("Can not bind tools and also use structured output.")

    def apply_capability(model: BaseChatModel):
        if schema:
            return model.with_structured_output(schema)
        if tools:
            return model.bind_tools(tools)
        return model

    primary_model = apply_capability(primary)
    fallback_models = [apply_capability(f) for f in fallbacks]

    def prepare_input(x: Any) -> Any:
        """Extracts the actual input from the wrapper dict if present."""
        if isinstance(x, dict) and "input" in x:
            return x["input"]
        return x

    primary_chain = RunnableLambda(prepare_input) | primary_model

    fallback_chains = []

    for i, model_to_use in enumerate(fallback_models):

        def create_log_wrapper(model_idx: int):
            def log_error(input_dict: dict):
                error = input_dict.get("error_info")
                prev_model = fallbacks[model_idx - 1] if model_idx != 0 else primary

                prev_name = getattr(prev_model, "model", str(prev_model))
                now_name = getattr(model_to_use, "model", str(model_to_use))

                logger.warning(
                    f"⚠️ Fallback triggered! Model attempt {model_idx} ({prev_name}) failed. Moving to {now_name}."
                )
                logger.debug(f"Error ({type(error).__name__}) w/ message: {str(error)}")

                return prepare_input(input_dict["input"])

            return log_error

        log_step = RunnableLambda(create_log_wrapper(i))
        fallback_chains.append(log_step | model_to_use)

    resilient_chain = primary_chain.with_fallbacks(
        fallback_chains, exception_key="error_info"
    )
    return RunnableLambda(lambda x: {"input": x}) | resilient_chain


gemini_2p5_flash = init_chat_model("gemini-2.5-flash", model_provider="google_genai")
gemini_3_flash = init_chat_model(
    "gemini-3-flash-preview", model_provider="google_genai"
)
gemini_2p5_flash_lite = init_chat_model(
    "gemini-2.5-flash-lite", model_provider="google_genai"
)
gemini_3p1_flash_lite = init_chat_model(
    "gemini-3.1-flash-lite", model_provider="google_genai"
)
gemma_4_31b = init_chat_model("gemma-4-31b-it", model_provider="google_genai")
