import pytest
import os
from pathlib import Path
from unittest.mock import MagicMock
from src.agents.tdd_lead import tdd_lead
from src.graph.state import AgentState

@pytest.mark.asyncio
async def test_tdd_lead_real_execution(tmp_path: Path):
    """
    Real execution test for TDD Lead.
    This test makes actual LLM calls and writes to a temporary directory.
    """
    # 1. Setup a dummy project structure
    working_dir = tmp_path / "my_project"
    src_dir = working_dir / "src"
    src_dir.mkdir(parents=True)
    
    # Create an initial empty class shell
    processor_file = src_dir / "processor.py"
    processor_file.write_text("class PaymentProcessor:\n    pass\n", encoding="utf-8")

    # 2. Prepare the Agent State with a realistic Use Case and Sequence Diagram
    state: AgentState = {
        "use_case": """
# Use Case: Process Payment
**Actors**: User, Payment Gateway (Secondary)
**Preconditions**: User has a valid cart.
**Main Success Scenario**:
1. User submits payment details.
2. System validates details.
3. System sends request to Payment Gateway.
4. System records transaction and returns success.
""",
        "sequence_diagram": """
sequenceDiagram
    participant U as User
    participant S as System
    participant G as Gateway
    U->>S: process_payment(details)
    S->>S: validate(details)
    S->>G: charge(amount)
    G-->>S: success
    S-->>U: confirmation
""",
        "messages": [],
        "user_intent_summary": None,
        "design_notes": None,
        "supervisor_phase": "APPROVAL",
        "critic_verdict": None,
        "critic_feedback": None,
        "revision_count": 0,
        "qa_messages": None,
        "qa_feedback": None,
        "qa_revision_count": 0
    }

    # 3. Mock the Runtime object to provide the working directory
    runtime_mock = MagicMock()
    runtime_mock.context = {"working_directory": working_dir}

    # 4. Invoke the TDD Lead agent (Real LLM call)
    print("\n[TDD Lead] Invoking real LLM...")
    # Note: tdd_lead returns the state, but its side effect is writing files to disk.
    await tdd_lead(state, runtime_mock)

    # 5. Validations
    print("[TDD Lead] Validating output...")
    
    # Check if test files were created
    test_dir = working_dir / "tests"
    assert test_dir.exists(), "Tests directory was not created."
    
    test_files = list(test_dir.glob("test_*.py"))
    assert len(test_files) > 0, "No test files were generated."
    
    # Check if conftest.py or test files have content
    for tf in test_files:
        content = tf.read_text(encoding="utf-8")
        assert len(content) > 50, f"Test file {tf.name} seems too short or empty."

    # Check if the source file was updated with stubs
    updated_content = processor_file.read_text(encoding="utf-8")
    # We expect the LLM to at least add one of the methods from the sequence diagram
    found_stub = any(m in updated_content for m in ["def process_payment", "def validate", "def charge"])
    assert found_stub, f"Source file was not updated with expected method stubs. Content:\n{updated_content}"

    print(f"[TDD Lead] Success! Generated {len(test_files)} test files and updated source stubs.")
