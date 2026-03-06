

# README

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
2. **Design Lab:**
    * **Analyst:** Drafts the "Fully Dressed" Use Case.
    * **Architect:** Maps the Use Case to a Mermaid Sequence Diagram.
    * **Critic:** Compares both for "Traceability" and logic errors.
    * *Loop:* If the Critic finds flaws, it sends the sequence diagram back for revision.
3. **Approval:** User reviews the synchronized Use Case and Diagram.
4. **Implementaiton:**
   * **Test Generation:** `QA Agent` writes tests based on the Use Case Extensions.
   * **Implementation:** `Engineer Agent` writes code to satisfy the tests and diagram.

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
