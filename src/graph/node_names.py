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
    PREPARE_DESIGN = "PrepareDesign"
    FINISH_DESIGN = "FinishDesign"
    PREPARE_IMPLEMENTATION = "PrepareImplementation"
    FINISH_IMPLEMENTATION = "FinishImplementation"
    PREPARE_FIX = "PrepareFix"
