import json

import pytest

from skill_fleet.core.hitl import (
    AutoApprovalHandler,
    create_feedback_handler,
)


def test_auto_approval_handler_approves_when_passed() -> None:
    handler = AutoApprovalHandler()
    feedback = handler.get_feedback(packaging_manifest="{}", validation_report={"passed": True})

    data = json.loads(feedback)
    assert data["status"] == "approved"
    assert data["reviewer"] == "system"


def test_auto_approval_handler_requests_revision_on_failure() -> None:
    handler = AutoApprovalHandler()
    feedback = handler.get_feedback(
        packaging_manifest="{}",
        validation_report={"passed": False, "status": "failed", "errors": ["e1", "e2", "e3", "e4"]},
    )

    data = json.loads(feedback)
    assert data["status"] == "needs_revision"
    assert "Validation errors" in data["comments"]
    assert data["reviewer"] == "system"


def test_create_feedback_handler_factory() -> None:
    assert isinstance(create_feedback_handler("auto"), AutoApprovalHandler)

    with pytest.raises(ValueError):
        create_feedback_handler("does_not_exist")
