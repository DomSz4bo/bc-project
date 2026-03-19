import os

from dotenv import load_dotenv
from langchain.chat_models import init_chat_model
from langchain_core.language_models.chat_models import BaseChatModel

load_dotenv()


def get_llm(
    model: str | None = None,
    provider: str | None = None,
    **kwargs,
) -> BaseChatModel:
    """
    Factory function to initialize a chat model.
    Defaults to environment variables if parameters are not provided.

    Args:
        model: The name of the model to use (e.g., "gemini-3.5-flash").
        provider: The model provider (e.g., "google_genai").
        **kwargs: Additional parameters passed to :func:`init_chat_model`.
    """
    model_name = model or os.getenv("LLM_MODEL", "gemma-3-27b-it")
    model_provider = provider or os.getenv("LLM_PROVIDER", "google_genai")

    return init_chat_model(
        model=model_name,
        model_provider=model_provider,
        **kwargs,
    )


default_llm = get_llm()
gemini_2p5_flash = get_llm("gemini-2.5-flash", "google_genai")
gemini_3_flash = get_llm("gemini-3-flash", "google_genai")
gemini_2p5_flash_lite = get_llm("gemini-2.5-flash-lite", "google_genai")
gemini_3_flash_lite = get_llm("gemini-3.1-flash-lite-preview", "google_genai")
