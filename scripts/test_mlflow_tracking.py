"""
Test script to verify MLflow DSPy autologging integration.

Run this script while MLflow UI is running to see traced DSPy operations.
"""

import dspy

from skill_fleet.services.monitoring import MLflowContext, setup_dspy_autologging

# Configure a simple LM with usage tracking
lm = dspy.LM("gemini/gemini-3-flash-preview", cache=False)
dspy.configure(lm=lm, track_usage=True)

# Setup MLflow autologging (no tracking_uri needed for local backend)
setup_dspy_autologging(
    experiment_name="skill-fleet-test",
)


# Test a simple DSPy program
class SimpleProgram(dspy.Module):
    """A simple DSPy program for testing MLflow tracking."""

    def forward(self, question: str) -> str:
        """Process a question."""
        pred = dspy.Predict("question -> answer")
        result = pred(question=question)
        return result.answer


# Run with MLflow context manager
with MLflowContext(
    run_name="test-dspy-tracking",
    tags={"phase": "test", "type": "simple"},
):
    # Create and run program
    program = SimpleProgram()
    result = program(question="What is 2 + 2?")
    print(f"Result: {result}")

print("\n✅ Test complete! Check http://localhost:5001 to see the traced run.")
