

# Project reference

THIS DOCUMENT IS A WORK IN PROGRESS AND IS OPEN TO CHANGES AS THE IMPLEMENTATION IS DEVELOPED.

**System Overview:** The project that is being developed is a research prototype for a "Visual-First" development pipeline that transforms ambiguous human intent into verified, test-driven code. The prototype centers on a **Multi-Agent Design Lab** where requirements are iteratively refined into a "Dual-Truth" contract: a textual **Cockburn Use Case** (Intent) and a visual **Mermaid Sequence Diagram** (Logic). By enforcing this rigorous design stage, the system ensures that subsequent **Test Generation (TDD)** and **Code Implementation** are strictly grounded in validated architectural logic rather than direct, unverified LLM generation.

---

## 🛠 Technology Stack

### Core Frameworks
* **Language:** Python 3.12+
* **UI/Frontend:** [Chainlit](https://docs.chainlit.io/) (Browser-based Chat Interface).
* **Orchestration:** [LangGraph](https://langchain-ai.github.io/langgraph/) (Stateful Multi-Agent Workflows).
* **LLM Framework:** [LangChain](https://python.langchain.com/).
* **Diagram Visualization:** [Mermaid.js](https://mermaid.js.org/intro/).

---

## 🔄 The AI Development Pipeline

1. **Intake:** User discusses the goal with the Supervisor.
2. **Design Lab:**
    * **Analyst:** Creates the Cockburn Use Case.
    * **Architect:** Maps the Use Case to a Mermaid Sequence Diagram.
    * **Critic:** Treats the Use Case as ground truth and audits the Diagram for faithful representation.
3. **Approval:** User reviews the synchronized Use Case and Diagram. Requests modifications or approves.
4. **Implementation:**
   * **Scaffolding:** Parses the Use Case and Sequence Diagram, creates the project directory structure, and writes empty class shells as stub files.
   * **Test Generation (TDD):** Writes tests covering the full Use Case — Main Success Scenario, Extensions, and Sequence Diagram interactions — adding function stubs to the scaffold as needed.
   * **Code Generation:** `Engineer` fills in the stub implementations to satisfy the test suite, using a `run_tests` tool to iteratively verify correctness.
   * **Test coverage:** `QA` verifies test code coverage and writes additional unit test if necessary.

---

## 🤖 Agent Architecture

The system uses the [subagents architecture](https://docs.langchain.com/oss/python/langchain/multi-agent/subagents) in LangChain/LangGraph where the central main agent coordinates the subagents. 

### 1. The Supervisor

* **Role:** Central orchestrator and user-facing conversational **agent**.
* **Responsibilities:**
  * talks to the user, helps the user clarify their goals and intent
  * initiates sub-agents based on the conversation


### 2. 🧪 The Design Lab
* a sub-agent of the system (name TBD), which is actually a sub-graph consisting of three nodes:

#### A. The Requirements Analyst

* **Role:** Translates user intent into structured business logic.
* **Responsibility:** Generates the **Cockburn "Sea-Level" Use Case**.

#### B. The System Architect

* **Role:** Technical modeler.
* **Responsibility:** Translates the Analyst's Use Case into **Mermaid.js Sequence Diagram** syntax.
* Mermaid sequence diagram syntax validation runs in a cycle until a correct diagram is created.

#### C. The Design Critic

* **Role:** Diagram auditor. The Use Case is treated as the validated ground truth and is not subject to critique.
* **Responsibility:** Verifies that the Sequence Diagram faithfully and completely represents the Use Case.


### 3. The Implementation Team

#### A. The Interface Scaffolder

* **Role:** Project scaffolding agent. First step of the Implementation pipeline.
* **Responsibility:** Translates the Sequence Diagram's structural information into a concrete project scaffold on disk. Provides a shared naming reference that both the TDD Lead and Engineer operate against, eliminating ambiguity about class and module names.

#### B. 📝 The TDD Lead

* **Role:** TDD Lead.
* **Responsibilit:** Create a test suite based on the system design (Use Case and Sequence Diagram) for the Engineer to implement against. 
* **Language/Framework:** Python + pytest. Tests follow pytest conventions.

#### C. 🔨 The Implementation Engineer

* **Role:** Full-stack Developer **agent**.
* **Responsibility:** Write the implementation of the designed system and use tests to verify the implementation.
* **Tools:** Filesystem access to read and edit scaffold files + `run_tests` tool to execute pytest and receive structured output.

### D. 📝 The QA

* **Role:** Quality assurance **agent**.
* **Responsibility:** Check test coverage and write additional unit tests if the coverage is not satisfactory.
* **Tools:** Filesystem access to read and edit test files + `run_tests_with_coverage` tool to get test results and coverage data.


---


## 📂 Project Structure
```text
bc-project/
├── .chainlit/                  # Chainlit configuration and translations
├── public/                     # Static assets for Chainlit
├── cli/
    ├── commands.py             # CLI command handlers
    ├── run_cli.py              # CLI entry point
    └── utils.py                # CLI utility functions
├── src/
│   ├── agents/                 # Node definitions for each agent
│   │   ├── supervisor.py       # Central orchestrator
│   │   ├── design_lab/         # Design Lab
│   │   │   ├── analyst.py      # Requirements analyst and Use Case Specialist
│   │   │   ├── architect.py    # Technical modeler
│   │   │   └── critic.py       # QA for design phase
│   │   ├── scaffolder.py       # Project scaffolding agent
│   │   ├── tdd_lead.py         # TDD test suite creator
│   │   └── engineer.py         # Code generator
│   │   ├── qa.py               # Test coverage enforcer
│   ├── graph/                  # LangGraph definitions
│   │   ├── state.py            # Graph state schema
│   │   └── workflow.py         # Graph construction and compilation
│   └── utils/                  # utility modules used in nodes
├── tests/                      # test suite
├── app.py                      # Chainlit UI and message handlers
├── chainlit.md                 # UI welcome screen content
└── AGENTS.md                   # Project reference
```

---

## 📝 Coding Standards

### Python & Chainlit
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
