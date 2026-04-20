
**System Overview**

This project is a research prototype for a **visual-first** development pipeline, designed to bridge the gap between ambiguous human intent and code. The system uses a **multi-agent** architecture, using LangGraph, to attempt to orchestrate a transition from an abstract idea to a concrete implementation.
The workflow is divided into two primary phases.

**The Design Lab:** A specialized team of agents works iteratively to refine a user goal into structured a **Cockburn Use Case** and synchronized **Mermaid Sequence Diagram**. This visual-first approach seeks to present the system's design using abstractions, enabling easier human validation before implementation begins.

**Implementation & Verification:** Once the design is approved, it serves as the "ground truth" for the implementation team. The system follows **TDD**-inspired aproach, by automatically generating class scaffolds and test suites before writing the application logic.

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

