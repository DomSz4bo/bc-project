---
name: agents-md-generator
description: Analyze a codebase and generate a high-quality, standardized AGENTS.md context file. Use this when asked to define agent roles, document coding standards, establish project architecture, or initialize an AGENTS.md file.
---

# AGENTS.md Generator Skill

This skill provides step-by-step instructions for analyzing a codebase and generating a comprehensive, high-quality `AGENTS.md` context file. An `AGENTS.md` file serves as the ultimate source of truth for coding agents operating in a repository, defining their personas, tech stack, constraints, communication protocols, and project-specific rules to prevent hallucinations and enforce existing patterns.

## Workflow: Discovery -> Planning -> Generation

### 1. Discovery Phase (Mandatory)
Before writing a single word of the `AGENTS.md` file, you MUST comprehensively scan the repository to infer the tech stack, architecture, and existing patterns.

**Actions:**
- Use search and file read tools to examine core configuration files (e.g., `package.json`, `requirements.txt`, `pom.xml`, `Cargo.toml`, `go.mod`, `docker-compose.yml`, `build.gradle`).
- Read existing `README.md`, `.env.example`, `.gitignore`, or documentation folders.
- Analyze the project directory structure to understand the architecture (e.g., frontend/backend separation, monorepo structure, service layers).
- Inspect test directories to determine the testing frameworks in use.
- Examine linting and formatting configs (e.g., `.eslintrc`, `pyproject.toml`, `.prettierrc`, `ruff.toml`) to extract established coding standards.

### 2. Planning Phase
Synthesize your findings from the Discovery Phase. Identify:
- The core mission and global context of the project.
- The precise languages, frameworks, testing libraries, and tools in use.
- What tools or approaches are explicitly NOT used (e.g., "Do not use npm, use pnpm exclusively").
- The logical agent personas/roles needed to operate within this specific architecture (e.g., "Frontend Specialist" for React, "QA Engineer" for pytest, "Lead Architect" for system design).

### 3. Generation Phase
Generate the `AGENTS.md` file using the established structure. You may use the provided template as a starting point, but you MUST fill it out with the specific details gathered during the Discovery Phase.

**Formatting Rules:**
- Write the `AGENTS.md` file in clean, structured Markdown.
- Use clear, authoritative imperatives (e.g., "Always use...", "Never modify...", "Must run tests before...").
- Ensure all constraints are explicit and unambiguous.

## Required `AGENTS.md` Sections

The generated `AGENTS.md` MUST include the following sections. A template is provided in `assets/AGENTS_TEMPLATE.md` which you should read and use as a baseline.

1. **Global Context & Mission:** A brief summary of what the project is and its primary goals.
2. **Tech Stack & Constraints:** Explicitly listed languages, frameworks, testing libraries, and tools. Crucially, it must tell agents what *not* to use.
3. **Agent Personas/Roles:** Define the specific roles needed for the repo. For each role, define their specific scope, allowed actions, and focus areas.
4. **Coding Standards & Conventions:** Rules around naming conventions, error handling, state management, and file structure.
5. **Workflow & Tool Usage:** How agents should interact with CLI tools, Git, or CI/CD pipelines.

## Accessing the Template
Read the template located at `assets/AGENTS_TEMPLATE.md` for the exact structural requirements and instructional tone. Copy its structure and populate it with the repository's context.
