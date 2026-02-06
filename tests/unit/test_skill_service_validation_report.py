"""Tests for skill_service validation report handling."""

import pytest

from skill_fleet.core.models import ValidationReport


@pytest.mark.asyncio
async def test_validation_report_handles_invalid_fields() -> None:
    """Test that validation report construction handles unexpected fields gracefully."""

    # Mock the workflow results with unexpected fields in validation_report
    phase3_result = {
        "validation_report": {
            "passed": True,
            "score": 0.85,
            "unexpected_field": "should_be_ignored",
            "another_unknown": {"nested": "data"},
        }
    }

    # The model_validate with strict=False should handle this
    raw_validation_report = phase3_result.get("validation_report")
    assert isinstance(raw_validation_report, dict)

    validation_report: ValidationReport | None = None
    passed = False
    try:
        validation_report = ValidationReport.model_validate(raw_validation_report, strict=False)
        passed = validation_report.passed
    except Exception as exc:
        # Fall back to dict's passed field if available
        passed = raw_validation_report.get("passed", False)
        pytest.fail(f"ValidationReport.model_validate raised exception: {exc}")

    assert validation_report is not None
    assert passed is True
    assert validation_report.passed is True


@pytest.mark.asyncio
async def test_validation_report_handles_validation_error() -> None:
    """Test that validation report falls back gracefully on validation error."""
    # Test with completely invalid data that would cause ValidationError
    raw_validation_report = {"invalid_structure_without_passed_field": True}

    validation_report: ValidationReport | None = None
    passed = False

    try:
        validation_report = ValidationReport.model_validate(raw_validation_report, strict=False)
        passed = validation_report.passed
    except Exception:
        # Fall back to dict's passed field if available
        passed = raw_validation_report.get("passed", False)

    # passed should be False since there's no "passed" key
    assert passed is False
    assert validation_report is None or validation_report.passed is False


@pytest.mark.asyncio
async def test_validation_report_handles_none() -> None:
    """Test that validation report handles None gracefully."""
    raw_validation_report = None

    validation_report: ValidationReport | None = None
    passed = False

    if isinstance(raw_validation_report, dict):
        try:
            validation_report = ValidationReport.model_validate(raw_validation_report, strict=False)
            passed = validation_report.passed
        except Exception:
            passed = raw_validation_report.get("passed", False)
    else:
        passed = False

    assert validation_report is None
    assert passed is False
