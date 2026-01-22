"""DSPy modules for skill creation workflow."""

from .ensemble import (
    BestOfN,
    EnsembleModule,
    MajorityVote,
)
from .error_handling import (
    RobustModule,
    ValidatedModule,
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
from .phase0_research import GatherExamplesModule as GatherExamplesModuleReAct
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
    # Phase 0 (Research)
    "GatherExamplesModuleReAct",
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
