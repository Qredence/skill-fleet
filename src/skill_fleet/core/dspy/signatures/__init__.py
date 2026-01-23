"""
DSPy signatures for skill creation workflow.

This module provides DSPy signature definitions organized by task:

**Task-Based Organization:**
- Task Analysis & Planning: Understanding intent, taxonomy placement, dependency analysis
- Content Generation: Skill content creation, section generation, capability implementation
- Quality Assurance: Validation, issue analysis, auto-fix generation, quality assessment
- Human-in-the-Loop: Checkpoints, clarifying questions, feedback processing
- Conversational Interface: Multi-turn conversation signatures
- Signature Optimization: Failure analysis, improvement proposals, version comparison
- Base: Core skill creation signatures (GatherExamples, UnderstandTask, PlanSkill, etc.)

**DSPy 3.1.2 Best Practices:**
- Signatures are organized by WHAT THEY DO, not WHEN they run
- Each signature is a reusable, composable unit
- Use `dspy.Signature` with clear Input/Output fields
- Leverage reasoning field for complex thinking when needed

**Import Examples:**
```python
# Task analysis signatures
from skill_fleet.core.dspy.signatures.task_analysis_planning import (
    GatherRequirements,
    AnalyzeIntent,
    FindTaxonomyPath,
)

# Content generation signatures
from skill_fleet.core.dspy.signatures.content_generation import (
    GenerateSkillContent,
    GenerateSkillSection,
)

# Quality assurance signatures
from skill_fleet.core.dspy.signatures.quality_assurance import (
    ValidateSkill,
    AssessSkillQuality,
)
```
"""

# Base signatures (core skill creation workflow)
from .base import (
    EditSkillContent,
    GatherExamplesForSkill,
    GenerateDynamicFeedbackQuestions,
    InitializeSkillSkeleton,
    IterateSkillWithFeedback,
    PackageSkillForApproval,
    PlanSkillStructure,
    UnderstandTaskForSkill,
)

# Conversational interface signatures (multi-turn conversation)
from .conversational_interface import (
    AssessReadiness as ConversationalAssessReadiness,
)
from .conversational_interface import (
    ConfirmUnderstandingBeforeCreation,
    DeepUnderstandingSignature,
    DetectMultiSkillNeeds,
    EnhanceSkillContent,
    GenerateClarifyingQuestion,
    InterpretUserIntent,
    PresentSkillForReview,
    ProcessUserFeedback,
    SuggestTestScenarios,
    VerifyTDDPassed,
)

# Human-in-the-loop signatures
from .human_in_the_loop import (
    AnalyzeFeedback,
    DetermineHITLStrategy,
    FormatValidationResults,
    GenerateClarifyingQuestions,
    GenerateHITLQuestions,
    GeneratePreview,
    GenerateRefinementPlan,
    SummarizeUnderstanding,
)
from .human_in_the_loop import (
    AssessReadiness as HITLAssessReadiness,
)

__all__ = [
    # Base signatures
    "GatherExamplesForSkill",
    "UnderstandTaskForSkill",
    "PlanSkillStructure",
    "InitializeSkillSkeleton",
    "EditSkillContent",
    "PackageSkillForApproval",
    "IterateSkillWithFeedback",
    "GenerateDynamicFeedbackQuestions",
    # Conversational interface
    "InterpretUserIntent",
    "DetectMultiSkillNeeds",
    "GenerateClarifyingQuestion",
    "ConversationalAssessReadiness",
    "DeepUnderstandingSignature",
    "ConfirmUnderstandingBeforeCreation",
    "PresentSkillForReview",
    "ProcessUserFeedback",
    "SuggestTestScenarios",
    "VerifyTDDPassed",
    "EnhanceSkillContent",
    # Human-in-the-loop
    "GenerateClarifyingQuestions",
    "GenerateHITLQuestions",
    "SummarizeUnderstanding",
    "GeneratePreview",
    "AnalyzeFeedback",
    "FormatValidationResults",
    "GenerateRefinementPlan",
    "HITLAssessReadiness",
    "DetermineHITLStrategy",
]

# Task-based signature modules are imported directly for clarity:
# from skill_fleet.core.dspy.signatures import task_analysis_planning
# from skill_fleet.core.dspy.signatures import content_generation
# from skill_fleet.core.dspy.signatures import quality_assurance
# from skill_fleet.core.dspy.signatures import signature_optimization
