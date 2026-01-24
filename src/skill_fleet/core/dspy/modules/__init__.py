"""DSPy modules for skill creation workflow."""

from .base import (
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
from .ensemble import (
    BestOfN,
    EnsembleModule,
    MajorityVote,
)
from .error_handling import (
    RobustModule,
    ValidatedModule,
)
from .generation import (
    ContentGeneratorModule,
    FeedbackIncorporatorModule,
    Phase2GenerationModule,
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
from .understanding import (
    DependencyAnalyzerModule,
    IntentAnalyzerModule,
    Phase1UnderstandingModule,
    PlanSynthesizerModule,
    RequirementsGathererModule,
    TaxonomyPathFinderModule,
)
from .validation import (
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
    # Ensemble methods
    "EnsembleModule",
    "BestOfN",
    "MajorityVote",
    # Error handling & robustness
    "RobustModule",
    "ValidatedModule",
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
