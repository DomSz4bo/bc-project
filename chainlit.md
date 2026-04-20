## System Overview:
This project is a research prototype for a "Visual-First" development pipeline that transforms ambiguous human intent into verified, test-driven code. The prototype centers on a **Multi-Agent** workflow. 

It starts by iteratively refining the intent and turning it into a textual **Use Case** and **Mermaid Sequence Diagram**. 
After the design is approved it moves to a **TDD** inspired test generation phase subsequently to a **Code Implementation** phase. Both are strictly grounded in the verified system design.

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

