---
name: project-readme-writer
description: Write or update a comprehensive README.md for a finished project that was built using the model-driven multi-agent workflow. It ensures the design artifacts (Cockburn Use Case and Mermaid Sequence Diagram) are incorporated into the README.
---

# Project README Writer

This skill guides the creation of a `README.md` file for projects developed using our multi-agent workflow. Projects generated this way always have design artifacts that serve as the basis for code generation.

## Process

1. **Locate Design Artifacts**: Before writing the README, search the project directory for the design artifacts. Look for:
   - The Cockburn Use Case (often named `use_case.md`, `usecase.md`, or similar).
   - The Mermaid Sequence Diagram (often named `sq_diagram.md`, `sequence_diagram.md`, or similar).
   - Any high-level description files (e.g., `description.md`).

2. **Understand the Project**: Read the found design artifacts to understand the project's intent (from the Use Case) and the technical logic (from the Sequence Diagram). Also, scan the project structure and source code to identify the technology stack, implementation details, and how to run/test the project.

3. **Draft the README.md**:
   Create a `README.md` with the following sections (adapt as needed based on the project):
   - **Project Title & Overview**: A brief summary of what the project does.
   - **Use Case**: Incorporate the Cockburn Use Case to explain the main user intent and scenarios. You can include it directly or summarize it if it's too long, but retain the core intent.
   - **Architecture & Logic**: Incorporate the Mermaid Sequence Diagram to visually show how the system operates. Use markdown mermaid blocks.
   - **Getting Started**: Instructions on how to set up the project locally.
   - **Usage**: Examples of how to use the application or system.
   - **Testing**: Instructions on how to run the test suite, emphasizing the TDD approach used during implementation.

4. **Formatting Guidelines**:
   - Use clear headings.
   - Embed Mermaid diagrams correctly using standard markdown code blocks tagged with `mermaid`.
   - Ensure the tone is professional and accurately reflects the design artifacts of the project.

5. **Review and Save**: After drafting, write the content to `README.md` in the root of the target project directory.