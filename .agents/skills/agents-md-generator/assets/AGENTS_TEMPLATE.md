# Repository Agent Guidelines

## 1. Global Context & Mission
[Provide a brief, clear summary of what this project is, its primary goals, and the problem it solves. Agents should read this to understand the broader context of their work.]

## 2. Tech Stack & Constraints
[Explicitly list all languages, frameworks, databases, testing libraries, and tooling.]

**Allowed Technologies:**
- **Language:** [e.g., Python 3.12+]
- **Frameworks:** [e.g., FastAPI, React]
- **Testing:** [e.g., pytest, Jest]
- **Package Manager:** [e.g., pnpm]

**Strict Constraints (DO NOT USE):**
- [e.g., "Do not use npm or yarn; use pnpm exclusively."]
- [e.g., "Do not use Tailwind CSS; use standard CSS Modules."]
- [e.g., "Never commit secrets or update the `.env` file directly."]

## 3. Agent Personas/Roles
[Define the specialized roles required for this repository. Assign boundaries and focuses to each.]

### [Role Name, e.g., "Lead Architect"]
- **Scope:** [e.g., System design, API contracts, database schemas.]
- **Allowed Actions:** [e.g., Modifying core domain models, approving PRs.]
- **Focus:** [e.g., Scalability, security, cross-module dependencies.]

### [Role Name, e.g., "Frontend Specialist"]
- **Scope:** [e.g., UI components, state management in React.]
- **Allowed Actions:** [e.g., Editing files in `/src/components` and `/src/hooks`.]
- **Focus:** [e.g., Accessibility, responsiveness, component reusability.]

### [Role Name, e.g., "QA Automation Engineer"]
- **Scope:** [e.g., Writing and maintaining the test suite.]
- **Allowed Actions:** [e.g., Editing files in `/tests/` and mocking fixtures.]
- **Focus:** [e.g., Achieving >90% code coverage, testing edge cases.]

## 4. Coding Standards & Conventions
[Establish strict rules for code formatting, architecture, and styling.]

- **Naming Conventions:** [e.g., Use snake_case for variables, PascalCase for classes.]
- **Error Handling:** [e.g., Always use try/catch blocks and log errors using the custom `logger` module.]
- **State Management:** [e.g., Use Redux Toolkit; do not use React Context for global state.]
- **File Structure:** [e.g., Place all interface definitions in `/types/`, not inline.]

## 5. Workflow & Tool Usage
[Detail how agents should execute commands, run tests, and interact with the system.]

- **CLI Commands:**
  - Build: `[e.g., pnpm build]`
  - Lint: `[e.g., ruff check .]`
  - Test: `[e.g., pytest --cov=src]`
- **Git Protocol:** [e.g., "Never push directly to main. Create a branch and issue a pull request."]
- **Tooling Directives:** [e.g., "Always use `run_shell_command` with `--silent` flag to run tests. Do not paginate terminal output."]
