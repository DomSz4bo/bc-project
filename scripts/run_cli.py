import asyncio
import json
import os
import uuid

from langchain_core.load import dumpd
from langchain_core.messages import AIMessage, HumanMessage
from prompt_toolkit import PromptSession
from prompt_toolkit.completion import WordCompleter
from prompt_toolkit.formatted_text import HTML
from prompt_toolkit.history import FileHistory
from prompt_toolkit.styles import Style

from src.graph.workflow import create_graph


def serialize_snapshot(snapshot):
    """
    Serializes a LangGraph StateSnapshot into a JSON-compatible dictionary.
    """
    return {
        "values": dumpd(snapshot.values),
        "next": snapshot.next,
        "config": snapshot.config,
        "metadata": snapshot.metadata,
    }


def save_to_json(data, filename):
    """
    Saves data to a pretty-printed JSON file in the current working directory.
    """
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    print(f"  ➜ Exported to: {filename}")



async def run_interactive_cli():
    """
    Runs an interactive CLI for testing the LangGraph workflow.
    """
    graph = create_graph()
    thread_id = str(uuid.uuid4())
    config = {"configurable": {"thread_id": thread_id}}
    thread_prefix = thread_id[:8]

    current_use_case = None
    current_sequence_diagram = None

    history_file = os.path.join(os.getcwd(), ".cli_history")
    commands = ["/exit", "/save", "/save-full"]
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
            f.write("# Design Lab Output\n\n")
            f.write("## Use Case\n\n")
            f.write(current_use_case or "Not yet generated.")
            f.write("\n\n## Sequence Diagram\n\n")
            if current_sequence_diagram:
                f.write("```mermaid\n")
                f.write(current_sequence_diagram)
                f.write("\n```\n")
            else:
                f.write("Not yet generated.")

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
                HTML("<prompt>User> </prompt>"),
                multiline=True,
                bottom_toolbar=get_toolbar,
            )

            user_input = user_input.strip()
            
            if not user_input:
                continue

            # Command Handling
            if user_input == "/exit":
                print("\nExiting. Goodbye!")
                break
            
            if user_input == "/save":
                print("\n" + "-" * 10 + " Exporting Current State " + "-" * 10)
                state = graph.get_state(config)
                filename = f"state_{thread_prefix}.json"
                save_to_json(serialize_snapshot(state), filename)
                print("-" * 40 + "\n")
                continue

            if user_input == "/save-full":
                print("\n" + "-" * 10 + " Exporting Full History " + "-" * 10)
                history = list(graph.get_state_history(config))
                filename = f"history_{thread_prefix}.json"
                serialized_history = [serialize_snapshot(s) for s in history]
                save_to_json(serialized_history, filename)
                print("-" * 40 + "\n")
                continue

            input_state = {"messages": [HumanMessage(content=user_input)]}

            print("\n" + "-" * 20 + " Workflow Execution " + "-" * 20)

            async for event in graph.astream(
                input_state,
                config=config,
                context={"max_revisions": 1},
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
            print("\nExiting. Goodbye!")
            break
        except Exception as e:
            print(f"\n❌ Error ({type(e).__name__}): {e}")


if __name__ == "__main__":
    try:
        asyncio.run(run_interactive_cli())
    except KeyboardInterrupt:
        pass
