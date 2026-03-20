import asyncio
import os
import uuid
from pathlib import Path

from langchain_core.messages import AIMessage, HumanMessage
from prompt_toolkit import PromptSession
from prompt_toolkit.completion import WordCompleter
from prompt_toolkit.formatted_text import HTML
from prompt_toolkit.history import FileHistory
from prompt_toolkit.styles import Style

from cli.commands import handle_exit, handle_save, handle_save_full
from src.graph.workflow import create_graph


async def run_interactive_cli():
    """
    Runs an interactive CLI for testing the LangGraph workflow.
    """
    graph = create_graph()
    thread_id = str(uuid.uuid4())
    config = {"configurable": {"thread_id": thread_id}}

    current_use_case = None
    current_sequence_diagram = None

    history_file = os.path.join(os.getcwd(), ".cli_history")

    commands_map = {
        "/exit": handle_exit,
        "/save": handle_save,
        "/save-full": handle_save_full,
    }

    commands = list(commands_map.keys())
    commands_completer = WordCompleter(commands, ignore_case=True, sentence=True)

    style = Style.from_dict(
        {
            "prompt": "ansicyan bold",
            "bottom-toolbar": "#6446A0",
            "key": "bold",
            "": "ansigreen",
        }
    )

    session = PromptSession(
        history=FileHistory(history_file),
        completer=commands_completer,
        complete_while_typing=True,
        style=style,
    )

    def save_output():
        with open("output.md", "w", encoding="utf-8") as f:
            f.write("# Design Lab Output\n\n## Use Case\n\n")
            f.write(current_use_case or "Not yet generated.")
            f.write("\n\n## Sequence Diagram\n\n")
            f.write(current_sequence_diagram or "Not yet generated.")

    def get_toolbar():
        return HTML(
            " Submit: <key>[Alt+Enter]</key> | "
            "New Line: <key>[Enter]</key> | "
            "<key>[Ctrl+D]</key> to quit "
        )

    print("=" * 50)
    print("🚀 WORKFLOW INTERACTIVE CLI")
    print(f"Session ID: {thread_id}")
    print(f"History saved to: {history_file}")
    print("=" * 50 + "\n")

    while True:
        try:
            user_input: str = await session.prompt_async(
                HTML("<prompt>User > </prompt>"),
                multiline=True,
                bottom_toolbar=get_toolbar,
            )

            user_input = user_input.strip()

            if not user_input:
                continue

            if user_input.startswith("/"):
                action = commands_map.get(user_input, None)
                if action:
                    should_exit = await action(graph=graph, config=config)
                    if should_exit:
                        break
                    continue
                else:
                    print(f"\033[91mUnknown command: {user_input}\033[0m")
                    continue

            input_state = {"messages": [HumanMessage(content=user_input)]}
            print("\n" + "-" * 20 + " Workflow Execution " + "-" * 20)

            graph_context = {"max_revisions": 1, "working_directory": Path.cwd()}

            async for event in graph.astream(
                input_state,
                config=config,
                context=graph_context,
                stream_mode="updates",
            ):
                for node_name, updates in event.items():
                    print(f"[{node_name}] running...")

                    if "next_step" in updates:
                        print(f"  ➜ next_step: {updates['next_step']}")
                    if "supervisor_phase" in updates:
                        print(f"  ➜ phase: {updates['supervisor_phase']}")
                    if "critic_verdict" in updates:
                        print(f"  ➜ critic: {updates['critic_verdict']}")
                    if "critic_feedback" in updates:
                        print(f"  ➜ feedback: {updates['critic_feedback']}")

                    if "use_case" in updates or "sequence_diagram" in updates:
                        if "use_case" in updates:
                            current_use_case = updates["use_case"]
                        if "sequence_diagram" in updates:
                            current_sequence_diagram = updates["sequence_diagram"]
                        save_output()
                        print("  ➜ Updated output.md")

                    if "messages" in updates:
                        last_msg = updates["messages"][-1]
                        if isinstance(last_msg, AIMessage):
                            print(f"\nAssistant: {last_msg.content}\n")

            print("-" * 60 + "\n")

        except KeyboardInterrupt:
            continue
        except EOFError:
            await handle_exit()
            break
        except Exception as e:
            print(f"\n❌ \033[91mError ({type(e).__name__}):\033[0m {e}")


def main():
    """Synchronous entry point for the CLI"""
    try:
        asyncio.run(run_interactive_cli())
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
