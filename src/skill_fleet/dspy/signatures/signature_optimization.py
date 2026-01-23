"""
Signature optimization DSPy signatures.

These signatures support the SignatureTuner module for analyzing
skill quality failures and proposing improved signatures through
metric-driven tuning.

Renamed from signature_tuning.py with clarified task-based naming.

Signatures:
- AnalyzeSignatureFailures: Analyze why a skill failed quality thresholds
- ProposeSignatureImprovement: Propose improved DSPy signature
- ValidateSignatureImprovement: Validate signature improvement safety
- CompareSignatureVersions: Compare signature versions for A/B testing
"""

from __future__ import annotations

# Re-export from existing location during migration
from skill_fleet.core.dspy.signatures.signature_tuning import (
    AnalyzeSignatureFailures,
    CompareSignatureVersions,
    ProposeSignatureImprovement,
    ValidateSignatureImprovement,
)

__all__ = [
    "AnalyzeSignatureFailures",
    "ProposeSignatureImprovement",
    "ValidateSignatureImprovement",
    "CompareSignatureVersions",
]
