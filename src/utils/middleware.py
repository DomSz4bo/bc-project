from typing import Any, Callable

from langchain.agents.middleware import AgentMiddleware, AgentState
from langchain.messages import ToolMessage
from langchain.tools.tool_node import ToolCallRequest
from langgraph.config import get_stream_writer
from langgraph.runtime import Runtime
from langgraph.types import Command
from loguru import logger

from src.utils.streaming import CustomStreamData


def format_tool_error(e: Exception) -> str:
    """
    Format a tool execution error with helpful hints.
    Suitable for use with ToolNode(handle_tool_errors=format_tool_error).
    """
    error_msg = str(e)
    hint = ""
    if "Could not find exact match for edit" in error_msg:
        hint = (
            "\nHint: The 'oldText' you provided did not perfectly match the file. "
            "Ensure you include all exact whitespace, indentation, and newlines. "
            "Consider using a read_file tool to get the exact text first."
        )

    return f"Tool execution failed: {error_msg}{hint}"


class LoggingMiddleware(AgentMiddleware):
    """Comprehensive logging middleware for agent execution."""

    def before_agent(
        self, state: AgentState, runtime: Runtime
    ) -> dict[str, Any] | None:
        logger.info("[Agent] Starting agent execution")
        return None

    def after_agent(self, state: AgentState, runtime: Runtime) -> dict[str, Any] | None:
        logger.info("[Agent] Finished agent execution")
        return None

    def before_model(
        self, state: AgentState, runtime: Runtime
    ) -> dict[str, Any] | None:
        messages = state.get("messages", [])
        if messages:
            last_message = messages[-1]
            logger.info(
                f"[Model] Call Starting - Last message type: {type(last_message).__name__}"
            )
        else:
            logger.info("[Model] Call Starting - No messages in state.")
        return None

    def after_model(self, state: AgentState, runtime: Runtime) -> dict[str, Any] | None:
        messages = state.get("messages", [])
        if messages:
            last_message = messages[-1]
            content = str(last_message.content)
            summary = content[:100] + "..." if len(content) > 100 else content
            logger.info(f"[Model] Call Completed - Returned (truncated): {summary}")
        return None

    def wrap_tool_call(
        self,
        request: ToolCallRequest,
        handler: Callable[[ToolCallRequest], ToolMessage | Command],
    ) -> ToolMessage | Command:
        tool_call = request.tool_call
        tool_name = tool_call.get("name", "Unknown")
        logger.info(f"[Tool] Starting execution: {tool_name}")
        logger.debug(f"[Tool] Arguments: {tool_call.get('args')}")
        try:
            result = handler(request)
            logger.info(f"[Tool] {tool_name} completed successfully.")
            return result
        except Exception as e:
            logger.error(f"[Tool] {tool_name} failed: {e}")
            raise

    async def abefore_agent(
        self, state: AgentState, runtime: Runtime
    ) -> dict[str, Any] | None:
        logger.info("[Agent] Starting agent execution (async)")
        return None

    async def aafter_agent(
        self, state: AgentState, runtime: Runtime
    ) -> dict[str, Any] | None:
        logger.info("[Agent] Finished agent execution (async)")
        return None

    async def abefore_model(
        self, state: AgentState, runtime: Runtime
    ) -> dict[str, Any] | None:
        messages = state.get("messages", [])
        if messages:
            last_message = messages[-1]
            logger.info(
                f"[Model] Call Starting (async) - Last message type: {type(last_message).__name__}"
            )
        else:
            logger.info("[Model] Call Starting (async) - No messages in state.")
        return None

    async def aafter_model(
        self, state: AgentState, runtime: Runtime
    ) -> dict[str, Any] | None:
        messages = state.get("messages", [])
        if messages:
            last_message = messages[-1]
            content = str(last_message.content)
            summary = content[:100] + "..." if len(content) > 100 else content
            logger.info(
                f"[Model] Call Completed (async) - Returned (truncated): {summary}"
            )
        return None

    async def awrap_tool_call(
        self,
        request: ToolCallRequest,
        handler: Callable,
    ) -> ToolMessage | Command:
        tool_call = request.tool_call
        tool_name = tool_call.get("name", "Unknown")
        logger.info(f"[Tool] Starting execution (async): {tool_name}")
        logger.debug(f"[Tool] Arguments (async): {tool_call.get('args')}")
        try:
            result = await handler(request)
            logger.info(f"[Tool] {tool_name} completed successfully (async).")
            return result
        except Exception as e:
            logger.error(f"[Tool] {tool_name} failed (async): {e}")
            raise


class ToolErrorMiddleware(AgentMiddleware):
    """
    Catch tool execution errors and return them to the agent.
    Useful for agents not using ToolNode or for more complex error wrapping.
    """

    def wrap_tool_call(
        self,
        request: ToolCallRequest,
        handler: Callable[[ToolCallRequest], ToolMessage | Command],
    ) -> ToolMessage | Command:
        try:
            return handler(request)
        except Exception as e:
            return ToolMessage(
                content=format_tool_error(e),
                tool_call_id=request.tool_call["id"],
            )

    async def awrap_tool_call(
        self,
        request: ToolCallRequest,
        handler: Callable,
    ) -> ToolMessage | Command:
        try:
            return await handler(request)
        except Exception as e:
            return ToolMessage(
                content=format_tool_error(e),
                tool_call_id=request.tool_call["id"],
            )


class ToolStreamingMiddleware(AgentMiddleware):
    """Custom data streaming middleware. Provides data about tool calls."""

    def wrap_tool_call(
        self,
        request: ToolCallRequest,
        handler: Callable[[ToolCallRequest], ToolMessage | Command],
    ) -> ToolMessage | Command:
        tool_call = request.tool_call
        tool_name = tool_call.get("name", "Unknown")

        result = handler(request)

        writer = get_stream_writer()
        msg = f"Executed tool call: {tool_name}\nResult:\n{result}"
        writer(CustomStreamData(msg, "message"))

        return result

    async def awrap_tool_call(
        self,
        request: ToolCallRequest,
        handler: Callable,
    ) -> ToolMessage | Command:
        tool_call = request.tool_call
        tool_name = tool_call.get("name", "Unknown")

        writer = get_stream_writer()
        writer(
            CustomStreamData(
                f"Executing tool call: {tool_name}", "start", {"spinner": "aesthetic"}
            )
        )

        result = await handler(request)

        msg = f"Executed tool call: {tool_name}\nResult:\n{result}"
        writer(CustomStreamData(msg, "end"))

        return result

