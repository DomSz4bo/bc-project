from enum import StrEnum


class Nodes(StrEnum):
    SUPERVISOR = "Supervisor"
    ANALYST = "Analyst"
    ARCHITECT = "Architect"
    CRITIC = "Critic"
    SCAFFOLDER = "Scaffolder"
    TDD = "TDD Lead"
    QA = "Quality assurance"
    ENGINEER = "Engineer"
    TOOLS = "tools"
    QA_TOOLS = "qa_tools"
    PREPARE_DESIGN = "prep_design"
    FINISH_DESIGN = "finish_design"
    PREPARE_IMPLEMENTATION = "prep_implementation"
    FINISH_IMPLEMENTATION = "finish_implementation"
    PREPARE_FIX = "prep_fix"
