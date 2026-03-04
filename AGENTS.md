

# Project reference

**System Overview:** This project is a research prototype for a "Visual-First" development pipeline that transforms ambiguous human intent into verified, test-driven code. The prototype centers on a **Multi-Agent Design Lab** where requirements are iteratively refined into a "Dual-Truth" contract: a textual **Cockburn Use Case** (Intent) and a visual **Mermaid Sequence Diagram** (Logic). By enforcing this rigorous design stage, the system ensures that subsequent **Test Generation (TDD)** and **Code Implementation** are strictly grounded in validated architectural logic rather than direct, unverified LLM generation.

---

## 🚀 Quickstart
```bash
conda env create -f environment.yaml
conda activate bc-project
chainlit run app.py
```

---

## 🔑 API Configuration
The project currently utilizes **Google Gemini** as the primary LLM provider.
1. Create a `.env` file in the root directory.
2. Add your API key: `GOOGLE_API_KEY=your_gemini_api_key_here`
3. Ensure the environment variable is loaded before running the application.

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
2. **Design Lab (Sub-graph):**
* **Analyst:** Drafts the "Fully Dressed" Use Case.
* **Architect:** Maps the Use Case to a Mermaid Sequence Diagram.
* **Critic:** Compares both for "Traceability" and logic errors.
* *Loop:* If the Critic finds flaws, it sends the pair back for revision.


3. **Approval:** User reviews the synchronized Use Case and Diagram.
4. **Test Gen:** `QA Agent` writes tests based on the Use Case Extensions.
5. **Implementation:** `Engineer Agent` writes code to satisfy the tests and diagram.

---

## 🤖 Agent Architecture

The system uses the [subagents architecture](https://docs.langchain.com/oss/python/langchain/multi-agent/subagents) in LangChain/LangGraph where the central main agent coordinates the subagents. 

### 1. The Supervisor (`@supervisor`)

* **Role:** High-level state manager.
* **Responsibility:** Talks to the user and orchestrates the subagents.
* **Decision Logic:** Determines if the system is in "Design Mode" (Design Lab), "Review Mode" (User Approval), or "Build Mode" (QA/Engineer).
* **Transition Logic:**
    * **User Intent** → Analyst (Initiates Design Lab).
    * **Use Case Created** → Architect.
    * **Diagram Created** → Critic.
    * **Critic `FAIL`** → Back to Architect (with feedback loop).
    * **Critic `PASS`** → User (for Approval).
    * **User `MODIFICATION`** → Back to Analyst with new User Intent. 
    * **User `APPROVED`** → QA Agent (Initiates Build Mode).
    * **Test Suite Created** → Engineer.

### 2. 🧪 The Design Lab (Sub-graph)

#### A. The Requirements Analyst (`@analyst`)

* **Role:** Translates user intent into structured business logic.
* **Responsibility:** Generates the **Cockburn "Sea-Level" Use Case**.
* **Focus:** Primary/Secondary Actors, Pre/Post-conditions, and the numbered Main Success Scenario.
* **Constraint:** Must define at least two "Extensions" (failure paths) for any complex goal.

#### B. The System Architect (`@architect`)

* **Role:** Technical modeler.
* **Responsibility:** Translates the Analyst's Use Case into **Mermaid.js Sequence Diagram** syntax.
* **Focus:** Participant lifecycle, message direction, and `alt`/`opt` logic blocks.
* **Constraint:** Every numbered step in the Analyst's Use Case must have a corresponding arrow in the Diagram.

#### C. The Design Critic (`@critic`)

* **Role:** Quality Assurance for the design phase.
* **Responsibility:** Compares the Use Case (Text) vs. the Diagram (Visual).
* **Output:** `PASS` (proceed to User) or `FAIL` (with specific instructions for the Analyst/Architect to fix).
* **Checklist:**
1. Do the Actors in the text match the Participants in the diagram?
2. Does every "Extension" in the Use Case have a matching `alt` block in the diagram?
3. Is the Mermaid syntax valid and renderable?

### 3. 📝 The QA Agent (`@qa`)

* **Role:** TDD Lead.
* **Inputs:** Validated Use Case + Diagram.
* **Outputs:** Test suite.
* **Logic:**
    * Uses **Preconditions** from the Use Case to set up test mocks.
    * Uses **Extensions** from the Use Case to define failure-case test functions.
    * Must verify **Success End Conditions** in the assertions.

### 4. 🔨 The Implementation Engineer (`@engineer`)

* **Role:** Full-stack Developer.
* **Inputs:** Validated Design + Test Suite.
* **Outputs:** Code.
* **Logic:** Implements classes/methods to pass the test suite while adhering to the Sequence Diagram flow.

---

## 📂 Project Structure
```text
bc-project/
├── .chainlit/                  # Chainlit configuration and translations
├── public/                     # Static assets for Chainlit
├── src/
│   ├── agents/                 # Node definitions for each agent
│   │   ├── supervisor.py       # Central orchestrator
│   │   ├── design_lab/         # Design Lab subgraph
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
* **Async/Await:** Use `async def` for all Chainlit message handlers and LangGraph nodes to ensure non-blocking UI.
* **Type Safety:** Use `Pydantic` models for all structured outputs.
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
