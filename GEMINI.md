# FlowSmith Project Context

**FlowSmith** is a research prototype for a "Visual-First IDE." It uses AI agents to iteratively refine software use cases via Sequence Diagrams before generating executable code.

## 🎯 Core Objectives
1.  **Visual Truth:** The Sequence Diagram (Mermaid.js) is the primary source of truth. Logic must be verified visually before code is written.
2.  **Iterative Refinement:** The workflow is cyclical: *Discuss -> Visualize -> Critique -> Refine*.
3.  **Supervisor Orchestration:** A "Supervisor" agent manages the state and delegation between specialized sub-agents.

---

## 🛠 Technology Stack

### Core Frameworks
* **Language:** Python 3.12+
* **UI/Frontend:** [Chainlit](https://docs.chainlit.io/) (Browser-based Chat Interface).
* **Orchestration:** [LangGraph](https://langchain-ai.github.io/langgraph/) (Stateful Multi-Agent Workflows).
* **LLM Framework:** [LangChain](https://python.langchain.com/).
* **Diagram Visualization:** [Mermaid.js](https://mermaid.js.org/intro/).

### Environment Management
* **Manager:** Conda.
* **Definition:** `environment.yml`.
* **Key Libs:** `chainlit`, `langgraph`, `langchain`, `langchain-google-genai`.

---

## 🤖 Agent Architecture (Supervisor Pattern)

The system uses a **Supervisor Node** in LangGraph to route messages between the user and specific worker agents.

### 1. Supervisor Agent
* **Role:** The Router / State Manager.
* **Responsibility:** Decides whether to route the conversation to the `Architect`, the `Engineer`, or return control to the User.
* **State:** Manages the global `AgentState` (conversation history, current diagram code, approval status).

### 2. The Architect (`@architect`)
* **Goal:** Refine the Use Case and Diagram.
* **Input:** Natural language requirements.
* **Output:** Strict **Mermaid.js Sequence Diagram** syntax.
* **Persona:** "Senior Systems Designer." Focuses on actors, async messages, `alt/else` error paths, and edge cases.
* **Constraint:** NEVER writes Python implementation code. Only diagrams.

### 3. The Engineer (`@engineer`)
* **Goal:** Implement the approved design.
* **Input:** A "Locked" Mermaid diagram + Technical constraints.
* **Output:** Python or relevant implementation code.
* **Persona:** "Senior Backend Developer." 
* **Constraint:** Writes code *exactly* matching the sequence diagram's flow. One class per participant, one method per arrow.

---

## 📝 Coding Standards

### Python & Chainlit
* **Async/Await:** Use `async def` for all Chainlit message handlers and LangGraph nodes to ensure non-blocking UI.
* **Type Safety:** Use `Pydantic` models for all structured outputs (e.g., structured diagram updates).
* **Chainlit UI:**
    * Use `cl.Message(content="...", elements=[...])` to send responses.
    * Wrap Mermaid code in triple backticks with the `mermaid` language tag:
        ```mermaid
        sequenceDiagram
            ...
        ```

### LangGraph Implementation
* **State Definition:** define a `TypedDict` or Pydantic model for `AgentState`.
* **Nodes:** Each agent is a graph node.
* **Edges:** Use conditional edges based on the Supervisor's routing decision.

## ⚠️ Research Constraints
* **Simplicity:** Do not introduce a database (PostgreSQL/Redis) unless strictly necessary for the graph memory (use `MemorySaver` for in-memory checks during dev).