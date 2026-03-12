

# Project reference

THIS DOCUMENT IS A WORK IN PROGRESS AND IS OPEN TO CHANGES AS THE IMPLEMENTATION IS DEVELOPED.

**System Overview:** This project is a research prototype for a "Visual-First" development pipeline that transforms ambiguous human intent into verified, test-driven code. The prototype centers on a **Multi-Agent Design Lab** where requirements are iteratively refined into a "Dual-Truth" contract: a textual **Cockburn Use Case** (Intent) and a visual **Mermaid Sequence Diagram** (Logic). By enforcing this rigorous design stage, the system ensures that subsequent **Test Generation (TDD)** and **Code Implementation** are strictly grounded in validated architectural logic rather than direct, unverified LLM generation.

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
* **Definition:** `environment.yaml`.
* **Key Libs:** `chainlit`, `langgraph`, `langchain`.

---

## 🔄 The AI Development Pipeline

1. **Intake:** User discusses the goal with the Supervisor.
2. **Design Lab:**
    * **Analyst:** Drafts the "Fully Dressed" Use Case.
    * **Architect:** Maps the Use Case to a Mermaid Sequence Diagram.
    * **Critic:** Treats the Use Case as ground truth and audits the Diagram for faithful representation.
    * *Loop:* On FAIL, the Critic routes the Diagram back to the Architect with specific revision instructions. The Analyst is not involved in this loop.
3. **Approval:** User reviews the synchronized Use Case and Diagram.
4. **Implementation:**
   * **Test Generation:** `QA Agent` writes tests based on the Use Case Extensions.
   * **Code Generation:** `Engineer Agent` writes code to satisfy the tests and diagram.

---

## 🤖 Agent Architecture

The system uses the [subagents architecture](https://docs.langchain.com/oss/python/langchain/multi-agent/subagents) in LangChain/LangGraph where the central main agent coordinates the subagents. 

### 1. The Supervisor

* **Role:** Central orchestrator and user-facing conversational agent.
* **Responsibility:** Manages the top-level state machine, conducts the requirements intake conversation, and routes between the Design Lab and Implementation teams based on gate conditions.
* **Intake Behavior:**
    * Engages the user in a structured dialogue to elicit a precise, unambiguous description of the desired goal.
    * Proactively offers suggestions, asks clarifying questions, and surfaces edge cases the user may not have considered.
    * Produces a **User Intent Summary** once the goal is internally consistent and sufficiently detailed — this summary is the sole input passed to the Design Lab.
* **Post-Design Behavior:**
    * Presents the validated Use Case and Sequence Diagram to the user for approval.
    * On `MODIFICATION`: synthesizes user feedback into an updated User Intent Summary and re-initiates the Design Lab from the Analyst.
    * On `APPROVED`: hands off the validated design to the QA Agent.
* **Transition Logic (Supervisor-owned gates only):**

| Condition | Next step |
|---|---|
| Intent Summary ready | `DESIGN` |
| `supervisor_phase == APPROVAL` | User (approval step) |
| User `MODIFICATION` | `DESIGN` (with revised intent) |
| User `APPROVED` | `IMPLEMENT` |

* **Phase Management:**
    * The Supervisor operates in two distinct phases, controlled by the `supervisor_phase` field in graph state.
    * `INTAKE`: Default phase. The Supervisor conducts the requirements conversation and produces the User Intent Summary.
    * `APPROVAL`: Entered when the Design Lab sets `supervisor_phase = APPROVAL` in graph state upon a Critic `PASS`. The Supervisor's system prompt is conditionally reconstructed to include the current Use Case and Sequence Diagram as read-only context, enabling it to present the design to the user and synthesize modification feedback accurately.

> `DESIGN` represents a transition the Design Lab workflow (Analyst -> Architect <-> Critic). \
`IMPLEMENT` represents a transition to the Implementation pipeline (QA -> Engineer)


### 2. 🧪 The Design Lab

#### A. The Requirements Analyst

* **Role:** Translates user intent into structured business logic.
* **Responsibility:** Generates the **Cockburn "Sea-Level" Use Case**.
* **Focus:** Primary/Secondary Actors, Pre/Post-conditions, and the numbered Main Success Scenario.

#### B. The System Architect

* **Role:** Technical modeler.
* **Responsibility:** Translates the Analyst's Use Case into **Mermaid.js Sequence Diagram** syntax.
* **Focus:** Participant lifecycle, message direction, and `alt`/`opt` logic blocks.
* **Tools:** Calls a Mermaid validation tool to confirm the diagram is syntactically correct and renderable before passing it to the Critic.

#### C. The Design Critic

* **Role:** Diagram auditor. The Use Case is treated as the validated ground truth and is not subject to critique.
* **Responsibility:** Verifies that the Sequence Diagram faithfully and completely represents the Use Case. The original User Intent Summary is not consulted — the Critic's sole reference frame is the Use Case as written.
* **Output:** `PASS` (proceed) or `FAIL` (with specific revision instructions routed exclusively to the Architect).
* **Checklist:**
  1. Do the Participants in the Diagram match the Actors declared in the Use Case?
  2. Does every numbered step in the Main Success Scenario have a corresponding arrow in the Diagram?
  3. Does every Extension in the Use Case have a corresponding alt block in the Diagram?


### 3. 📝 The QA Agent

* **Role:** TDD Lead.
* **Inputs:** Validated Use Case + Diagram.
* **Outputs:** Test suite.
* **Logic:**
    * Uses **Preconditions** from the Use Case to set up test mocks.
    * Uses **Extensions** from the Use Case to define failure-case test functions.
    * Must verify **Success End Conditions** in the assertions.

### 4. 🔨 The Implementation Engineer

* **Role:** Full-stack Developer.
* **Inputs:** Validated Design + Test Suite.
* **Outputs:** Code.
* **Logic:** Implements classes/methods to pass the test suite while adhering to the Sequence Diagram flow.

---

## 💾 Graph State Schema

Defined in `src/graph/state.py`. All agents read from and write to this shared state.

#### `AgentState`

The primary state object threaded through the entire graph.

| Field | Type | Description |
|---|---|---|
| `messages` | `list[AnyMessage]` | Full conversation history, managed via LangGraph's `add_messages` reducer. |
| `next_step` | `"DESIGN" \| "IMPLEMENT" \| "USER" \| None` | Supervisor-owned routing signal. |
| `user_intent_summary` | `str \| None` | Structured User Intent Summary produced by the Supervisor, passed as the sole input to the Design Lab. |
| `supervisor_phase` | `"INTAKE" \| "APPROVAL"` | Controls Supervisor behavior and prompt construction. Defaults to `INTAKE`; set to `APPROVAL` by the Design Lab. |
| `use_case` | `str \| None` | Current Cockburn Use Case produced by the Analyst. |
| `sequence_diagram` | `str \| None` | Current Mermaid Sequence Diagram produced by the Architect. |
| `critic_status` | `"PASS" \| "FAIL" \| None` | Internal Design Lab signal. Not consumed by the Supervisor. |
| `critic_feedback` | `str \| None` | Specific revision instructions from the Critic on `FAIL`, routed back to the Architect. |
| `iteration_count` | `int` | Tracks Design Lab revision cycles. Guards against infinite Critic loops; compared against `GraphContext.max_iters`. |
| `test_suite` | `str \| None` | Test suite produced by the QA Agent, passed to the Engineer. |
| `final_code` | `str \| None` | Output code produced by the Engineer. |

#### `GraphContext`

Static configuration passed at graph compile time, not modified during execution.

| Field | Type | Description |
|---|---|---|
| `max_iters` | `int` | Maximum number of Critic revision cycles before the Design Lab halts and surfaces the issue to the user. |

---

## 📂 Project Structure
```text
bc-project/
├── .chainlit/                  # Chainlit configuration and translations
├── public/                     # Static assets for Chainlit
├── src/
│   ├── agents/                 # Node definitions for each agent
│   │   ├── supervisor.py       # Central orchestrator
│   │   ├── design_lab/         # Design Lab
│   │   │   ├── analyst.py      # Requirements analyst and Use Case Specialist
│   │   │   ├── architect.py    # Technical modeler
│   │   │   └── critic.py       # QA for design phase
│   │   ├── qa.py               # Test suite creator
│   │   └── engineer.py         # Code generator
│   └── graph/                  # LangGraph definitions
│       ├── state.py            # Graph state schema
│       └── workflow.py         # Graph construction and compilation
├── app.py                      # Chainlit UI and message handlers
├── chainlit.md                 # UI welcome screen content
├── environment.yaml            # Conda environment
└── AGENTS.md                   # Project reference
```

---

## 📝 Coding Standards

### Python & Chainlit
* **Keys:** Use the `state["<key>"]` syntax instead of `state.get("<key>")` when possible.
* **Async/Await:** Use `async def` for all Chainlit message handlers and LangGraph nodes to ensure non-blocking UI.
* **Type Safety:** Use `Pydantic` models for all structured outputs.
* **Typing**: Use the modern `type | None` syntax instead of `Optional`.
* **Chainlit UI:**
    * Use `cl.Message(content="...", elements=[...])` to send responses.
    * Wrap Mermaid code in triple backticks with the `mermaid` language tag:
        ```mermaid
        sequenceDiagram
          Alice->>+John: Hello John, how are you?
          Alice->>+John: John, can you hear me?
          John-->>-Alice: Hi Alice, I can hear you!
          John-->>-Alice: I feel great!!
        ```
* **Supervisor Prompt Construction:**
    * Build the Supervisor's system prompt conditionally based on `supervisor_phase` from graph state.
    * In `APPROVAL` phase, append the current design as a read-only block:
    ```
        [CURRENT DESIGN]
        Use Case:
        {use_case}

        Sequence Diagram:
        {sequence_diagram}
    ```