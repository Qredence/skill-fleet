"""DSPy modules for skill creation workflow."""

from .base import (
    DynamicQuestionGeneratorModule,
    EditModule,
    EditModuleQA,
    GatherExamplesModule,
    InitializeModule,
    IterateModule,
    PackageModule,
    PackageModuleQA,
    PlanModule,
    PlanModuleQA,
    UnderstandModule,
    UnderstandModuleQA,
)
from .hitl import (
    ClarifyingQuestionsModule,
    ConfirmUnderstandingModule,
    FeedbackAnalyzerModule,
    HITLStrategyModule,
    PreviewGeneratorModule,
    ReadinessAssessorModule,
    RefinementPlannerModule,
    ValidationFormatterModule,
)
from .phase1_understanding import (
    DependencyAnalyzerModule,
    IntentAnalyzerModule,
    Phase1UnderstandingModule,
    PlanSynthesizerModule,
    RequirementsGathererModule,
    TaxonomyPathFinderModule,
)
from .phase2_generation import (
    ContentGeneratorModule,
    FeedbackIncorporatorModule,
    Phase2GenerationModule,
)
from .phase3_validation import (
    Phase3ValidationModule,
    QualityAssessorModule,
    SkillRefinerModule,
    SkillValidatorModule,
)

__all__ = [
    # Base modules (legacy workflow)
    "GatherExamplesModule",
    "UnderstandModule",
    "PlanModule",
    "InitializeModule",
    "EditModule",
    "PackageModule",
    "IterateModule",
    "UnderstandModuleQA",
    "PlanModuleQA",
    "EditModuleQA",
    "PackageModuleQA",
    "DynamicQuestionGeneratorModule",
    # HITL modules
    "ClarifyingQuestionsModule",
    "ConfirmUnderstandingModule",
    "PreviewGeneratorModule",
    "FeedbackAnalyzerModule",
    "ValidationFormatterModule",
    "RefinementPlannerModule",
    "ReadinessAssessorModule",
    "HITLStrategyModule",
    # Phase 1 modules
    "RequirementsGathererModule",
    "IntentAnalyzerModule",
    "TaxonomyPathFinderModule",
    "DependencyAnalyzerModule",
    "PlanSynthesizerModule",
    "Phase1UnderstandingModule",
    # Phase 2 modules
    "ContentGeneratorModule",
    "FeedbackIncorporatorModule",
    "Phase2GenerationModule",
    # Phase 3 modules
    "SkillValidatorModule",
    "SkillRefinerModule",
    "QualityAssessorModule",
    "Phase3ValidationModule",
]
