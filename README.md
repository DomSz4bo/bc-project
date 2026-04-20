
# README

**System Overview**

This project is a research prototype for a **visual-first** development pipeline, designed to bridge the gap between ambiguous human intent and code. The system uses a **multi-agent** architecture, using LangGraph, to attempt to orchestrate a transition from an abstract idea to a concrete implementation.
The workflow is divided into two primary phases.

**The Design Lab:** A specialized team of agents works iteratively to refine a user goal into structured a **Cockburn Use Case** and synchronized **Mermaid Sequence Diagram**. This visual-first approach seeks to present the system's design using abstractions, enabling easier human validation before implementation begins.

**Implementation & Verification:** Once the design is approved, it serves as the "ground truth" for the implementation team. The system follows **TDD**-inspired aproach, by automatically generating class scaffolds and test suites before writing the application logic.

---

## 🚀 Quickstart

### Option A: Using Conda (Recommended)
```bash
conda env create -f environment.yaml
conda activate bc-project
bc-app
```

### Option B: Using standard Python (venv/uv)
```bash
python -m venv .venv
source .venv/bin/activate  # or .venv\Scripts\activate on Windows
pip install -e .
bc-app
```

---

## 🔑 API Configuration
The project currently utilizes **Google Gemini** as the sole LLM provider.
1. Create a `.env` file in the root directory.
2. Add your API key: `GOOGLE_API_KEY=your_gemini_api_key_here`

---

## 🛠 Technology Stack

### Core Frameworks
* **Language:** Python 3.12+
* **Orchestration:** [LangGraph](https://langchain-ai.github.io/langgraph/) (Stateful Multi-Agent Workflows).
* **LLM Framework:** [LangChain](https://python.langchain.com/).
* **Diagram Visualization:** [Mermaid.js](https://mermaid.js.org/intro/).
* **Browser-based Chat Interface:** [Chainlit](https://docs.chainlit.io/).

### Environment Management
* **Manager:** Conda.
* **Definition:** `environment.yaml`.
* **Key Libs:** `chainlit`, `langgraph`, `langchain`.

---

## 🔄 The AI Workflow

1. **Intake:** User discusses the goal with the Supervisor.
2. **Design Lab:**
    * **`Analyst`:** Creates the Use Case.
    * **`Architect`:** Maps the Use Case to a Mermaid Sequence Diagram.
    * **`Critic`:** Compares the two design artifacts and searches for errors.
    * *Loop:* If the Critic finds flaws, it sends the **sequence diagram** back for revision.
3. **Approval:** User reviews the synchronized Use Case and Diagram.
4. **Implementation:**
   * **Ground truth:** `Scaffolder` creates class stubs (.py files) based on the design artifacts.
   * **Test Generation:** `TDD Lead` writes initial tests based on the Use Case Extensions and Sequence diagram.
   * **Implementation:** `Engineer Agent` writes code to satisfy the tests and design.
   * **Validation:** `QA agent` checks test coverage and proposes new tests accordingly. Can send the implementation back to the `Engineer` for fixing.

---

## Workflow scheme
![Workflow diagram](https://www.st.fmph.uniba.sk/~szabo175/assets/workflow_scheme.jpeg)


---

## 📂 Project Structure
```text
bc-project/
├── .agents/skills/                 # app-global supervisor (post-impl.) skills
├── .chainlit/                      # Chainlit configuration and translations
├── public/                         # Static assets for Chainlit
├── cli/
│   ├── commands.py                 # CLI command handlers
│   ├── run_cli.py                  # CLI
│   ├── run_app.py                  # APP entry point
│   └── utils.py                    # CLI utility functions
├── src/
│   ├── agents/                     # Node definitions for each agent
│   │   ├── supervisor.py           # Central orchestrator
│   │   ├── design_lab/             # Design Lab
│   │   │   ├── analyst.py          # Requirements analyst and Use Case Specialist
│   │   │   ├── architect.py        # Technical modeler
│   │   │   └── critic.py           # QA for design phase
│   │   ├── scaffolder.py           # Project scaffolding agent
│   │   ├── tdd_lead.py             # TDD test suite creator
│   │   └── engineer.py             # Code generator
│   │   ├── qa.py                   # Test coverage enforcer
│   ├── graph/                      
│   │   ├── util_nodes/             # state transition handler nodes
│   │   │   ├── design.py
│   │   │   └── implementation.py
│   │   ├── node_names.py           # Node name enum definition
│   │   ├── state.py                # Graph state and context schema
│   │   └── workflow.py             # Graph construction and compilation
│   └── utils/                      # utility modules used in nodes
│       ├──
├── tests/                          # test suite
├── app.py                          # Chainlit UI
└── chainlit.md                     # UI welcome screen content
```
