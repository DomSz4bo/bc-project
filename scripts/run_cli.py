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
                    if "use_case" in updates:
                        print(f"\n--- USE CASE ---\n{updates['use_case']}\n")
                    if "sequence_diagram" in updates:
                        print(
                            f"\n--- SEQUENCE DIAGRAM ---\n{updates['sequence_diagram']}\n"
                        )

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
