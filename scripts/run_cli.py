import asyncio
import uuid

from langchain_core.messages import AIMessage, HumanMessage

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

    print("=" * 50)
    print("🚀 WORKFLOW INTERACTIVE CLI")
    print(f"Session ID: {thread_id}")
    print("Type 'exit', 'quit', or 'q' to stop.")
    print("=" * 50 + "\n")

    while True:
        try:
            user_input = input("User: ")
            if user_input.lower() in ["exit", "quit", "q"]:
                print("\nExiting. Goodbye!")
                break

            if not user_input.strip():
                continue

            input_state = {"messages": [HumanMessage(content=user_input)]}

            print("\n" + "-" * 20 + " Workflow Execution " + "-" * 20)

            # Using astream with stream_mode="values" to see the full state updates
            # or stream_mode="updates" to see only what changed.
            # "values" is often easier for tracking the message list.
            async for event in graph.astream(
                input_state, config=config, context={"max_revisions": 1}, stream_mode="updates"
            ):
                for node_name, updates in event.items():
                    print(f"[{node_name}] running...")

                    # Print interesting state changes
                    if "next_step" in updates:
                        print(f"  ➜ next_step: {updates['next_step']}")
                    if "supervisor_phase" in updates:
                        print(f"  ➜ phase: {updates['supervisor_phase']}")
                    if "critic_verdict" in updates:
                        print(f"  ➜ critic: {updates['critic_verdict']}")
                    if "critic_feedback" in updates:
                        print(f"  ➜ feedback: {updates['critic_feedback']}")

                    # Update output.md if design elements changed
                    if "use_case" in updates or "sequence_diagram" in updates:
                        if "use_case" in updates:
                            current_use_case = updates["use_case"]
                        if "sequence_diagram" in updates:
                            current_sequence_diagram = updates["sequence_diagram"]
                        save_output()
                        print("  ➜ Updated output.md")

                    # If the node added messages, print the last one (the AI response)
                    if "messages" in updates:
                        last_msg = updates["messages"][-1]
                        if isinstance(last_msg, AIMessage):
                            print(f"\nAssistant: {last_msg.content}\n")

            print("-" * 60 + "\n")

        except KeyboardInterrupt:
            print("\nExiting. Goodbye!")
            break
        except Exception as e:
            print(type(e))
            print(f"\n❌ Error: {e}")


if __name__ == "__main__":
    try:
        asyncio.run(run_interactive_cli())
    except KeyboardInterrupt:
        pass
