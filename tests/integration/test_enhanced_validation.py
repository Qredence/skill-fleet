#!/usr/bin/env python3
"""Integration tests for enhanced validation pipeline.

Tests the new validation features added in the skill-fleet improvements:
- Structure validation
- Test case generation
- Quality metrics (size, verbosity)
- Template compliance
- End-to-end validation workflow
"""

import asyncio
from unittest.mock import patch

import dspy
import pytest


class MockLM(dspy.LM):
    """Mock LM for predictable validation testing."""

    def __init__(self):
        super().__init__(model="mock/model")

    def __call__(self, prompt=None, messages=None, **kwargs):
        """Mock LLM responses based on prompt content."""
        prompt_str = str(prompt or messages or "").lower()

        # Structure validation
        if "structure" in prompt_str and ("name" in prompt_str or "description" in prompt_str):
            return self._mock_structure_response(prompt_str)

        # Test case generation
        if "test" in prompt_str and ("trigger" in prompt_str or "positive" in prompt_str):
            return self._mock_test_cases_response()

        # Compliance validation
        if "compliance" in prompt_str or "yaml" in prompt_str or "frontmatter" in prompt_str:
            return self._mock_compliance_response()

        # Quality assessment
        if "quality" in prompt_str or ("assess" in prompt_str and "content" in prompt_str):
            return self._mock_quality_response()

        # Template validation
        if "template" in prompt_str:
            return self._mock_template_response()

        # Refinement
        if "refine" in prompt_str or "improve" in prompt_str:
            return self._mock_refinement_response()

        # Metrics collection
        if "baseline" in prompt_str:
            return self._mock_baseline_metrics_response()
        if "skill" in prompt_str and "metric" in prompt_str:
            return self._mock_skill_metrics_response()
        if "compare" in prompt_str:
            return self._mock_comparison_response()

        # Content generation
        if "generate" in prompt_str and "content" in prompt_str:
            return self._mock_content_generation_response()

        return self._mock_default_response()

    def _mock_structure_response(self, prompt_str: str) -> str:
        """Mock structure validation response."""
        # Check if testing invalid skill
        if "invalid" in prompt_str or "bad" in prompt_str:
            return """name_valid: false
name_errors: ["Name contains invalid characters", "Name should be kebab-case"]
description_valid: false
description_errors: ["Description too short (min 50 chars)", "Missing trigger phrase examples"]
description_warnings: ["Consider adding more specific use cases"]
security_issues: ["Description mentions sensitive data without security context"]
suggested_skill_name: valid-skill-name
suggested_description: Use when you need to create a valid skill with proper kebab-case naming and comprehensive description."""

        # Valid skill
        return """name_valid: true
name_errors: []
description_valid: true
description_errors: []
description_warnings: []
security_issues: []
suggested_skill_name: ""
suggested_description: ""
"""

    def _mock_test_cases_response(self) -> str:
        """Mock test case generation response."""
        return """positive_tests:
  - "How do I create a React component with TypeScript?"
  - "Build a reusable button component in React"
  - "Create a form component with validation in TypeScript"
  - "I need to build a React component library"
negative_tests:
  - "How do I create a Vue component?"
  - "Build an Angular directive"
  - "Create a Python Flask API"
  - "Set up a database in PostgreSQL"
edge_cases:
  - "Create a React component in JavaScript (not TypeScript)"
  - "Convert existing React JS component to TypeScript"
  - "Create a React component with both TypeScript and JavaScript"
functional_tests:
  - "Given a design mock, generate TypeScript React component code"
  - "Component should compile without TypeScript errors"
  - "Component should follow React best practices"
"""

    def _mock_compliance_response(self) -> str:
        """Mock compliance validation response."""
        return """passed: true
compliance_score: 0.92
issues: []
critical_issues: []
warnings: ["Consider adding more detailed examples"]
auto_fixable: []"""

    def _mock_quality_response(self) -> str:
        """Mock quality assessment response."""
        return """overall_score: 0.85
completeness: 0.9
clarity: 0.88
usefulness: 0.87
accuracy: 0.92
strengths: ["Clear examples", "Good TypeScript coverage", "Practical patterns"]
weaknesses: ["Could use more edge case coverage", "Introduction could be more concise"]
meets_success_criteria: ["Code examples work", "TypeScript types are correct"]
missing_success_criteria: ["Edge case documentation"]"""

    def _mock_template_response(self) -> str:
        """Mock template validation response."""
        return """compliance_score: 0.88
sections_present: ["## Output Format", "## Style Guidelines", "## Examples"]
missing_sections: []
required_elements_present: ["template", "style_guide"]
missing_elements: []
format_compliance: true"""

    def _mock_refinement_response(self) -> str:
        """Mock refinement response."""
        return """refined_content: "# Refined Skill\\n\\nImproved content with better organization and clearer examples."
improvements_made: ["Reorganized sections for clarity", "Added more examples", "Improved TypeScript coverage"]
new_score_estimate: 0.92
requires_another_pass: false"""

    def _mock_baseline_metrics_response(self) -> str:
        """Mock baseline metrics collection response."""
        return """tool_calls: 12
api_failures: 3
tokens_consumed: 6000
interaction_turns: 10
success_rate: 0.55
reasoning: "Without skill guidance, agent needs to explore, makes API errors, and requires more turns to complete task."""

    def _mock_skill_metrics_response(self) -> str:
        """Mock skill-assisted metrics collection response."""
        return """tool_calls: 5
api_failures: 0
tokens_consumed: 2500
interaction_turns: 4
success_rate: 0.95
reasoning: "With skill guidance, agent follows proven pattern, reduces errors, and completes task efficiently."""

    def _mock_comparison_response(self) -> str:
        """Mock metrics comparison response."""
        return """token_reduction: 0.58
api_failure_reduction: 3
interaction_reduction: 6
success_rate_change: 0.4
meets_targets: true
recommendations: ["Skill performs well across all metrics. No major improvements needed."]"""

    def _mock_content_generation_response(self) -> str:
        """Mock content generation response."""
        return """skill_content: "---\\nid: test-skill\\nname: Test Skill\\n---\\n\\n# Test Skill\\n\\nUse when testing skill generation.\\n\\n## Output Format\\n\\nOutput should be structured.\\n\\n## Examples\\n\\nExample code here."
sections_generated: ["Output Format", "Examples"]
code_examples_count: 2
estimated_reading_time: 5
success: true
rationale: "Content follows template structure."""

    def _mock_default_response(self) -> str:
        """Default mock response."""
        return "Default mock response"


@pytest.fixture
def mock_lm():
    """Fixture to setup mock LM for tests."""
    mock = MockLM()
    dspy.configure(lm=mock)
    return mock


@pytest.fixture
def sample_skill_content():
    """Fixture providing a sample valid skill content."""
    return """---
id: react-component-typescript
name: react-component-typescript
description: Use when you need to create a React component with TypeScript. Helps when building reusable components, implementing type-safe props, or setting up component patterns.
trigger_patterns:
  - "create react component"
  - "typescript component"
  - "react typescript"
category: technical
---

# React Component with TypeScript

Use this skill when you need to build production-ready React components with full TypeScript support.

## When to Use

- Creating new React components
- Converting JavaScript components to TypeScript
- Implementing reusable component patterns
- Setting up component libraries

## Output Format

```typescript
interface ComponentProps {
  // Define all props with types
}

export const Component: React.FC<ComponentProps> = (props) => {
  // Implementation
};
```

## Examples

### Basic Component

```typescript
interface ButtonProps {
  label: string;
  onClick: () => void;
  variant?: 'primary' | 'secondary';
}

export const Button: React.FC<ButtonProps> = ({
  label,
  onClick,
  variant = 'primary'
}) => {
  return (
    <button className={`btn btn-${variant}`} onClick={onClick}>
      {label}
    </button>
  );
};
```
"""


@pytest.fixture
def sample_plan():
    """Fixture providing a sample skill plan."""
    return {
        "skill_name": "react-component-typescript",
        "skill_description": "Use when you need to create a React component with TypeScript. Helps when building reusable components.",
        "taxonomy_path": "technical/frontend/react",
        "content_outline": ["Introduction", "Setup", "Examples"],
        "success_criteria": ["Code compiles", "Follows best practices"],
        "trigger_phrases": ["create react component", "typescript component"],
        "negative_triggers": ["vue component", "angular"],
        "skill_category": "document_creation",
    }


# =============================================================================
# Test Structure Validation
# =============================================================================


class TestStructureValidation:
    """Tests for structure validation module and workflow integration."""

    def test_valid_skill_passes_structure_validation(self, mock_lm):
        """Test that a valid skill passes structure validation quickly."""
        from skill_fleet.core.modules.validation.structure import ValidateStructureModule

        module = ValidateStructureModule()

        result = module.forward(
            skill_name="valid-skill-name",
            description="Use when you need to create a valid skill. This is a comprehensive description with more than fifty characters.",
            skill_content="# Valid Skill\n\nValid content here.",
        )

        assert result["overall_valid"] is True
        assert len(result["name_errors"]) == 0
        assert len(result["description_errors"]) == 0

    def test_invalid_skill_triggers_structure_errors(self, mock_lm):
        """Test that invalid skill names trigger appropriate errors."""
        from skill_fleet.core.modules.validation.structure import ValidateStructureModule

        module = ValidateStructureModule()

        # Test with invalid name (not kebab-case)
        result = module.forward(
            skill_name="InvalidSkillName",
            description="Too short",
            skill_content="# Invalid",
        )

        # The rule-based validation should catch this even without LLM
        assert result["name_valid"] is False
        assert any("kebab" in err.lower() for err in result["name_errors"])

    def test_kebab_case_validation(self):
        """Test the kebab-case validation regex pattern."""
        from skill_fleet.core.modules.validation.structure import ValidateStructureModule

        module = ValidateStructureModule()

        # Valid kebab-case names
        assert module._is_valid_kebab_case("valid-skill") is True
        assert module._is_valid_kebab_case("skill-name-123") is True
        assert module._is_valid_kebab_case("a-b-c") is True

        # Invalid names
        assert module._is_valid_kebab_case("InvalidSkill") is False
        assert module._is_valid_kebab_case("skill_name") is False
        assert module._is_valid_kebab_case("-invalid-start") is False
        assert module._is_valid_kebab_case("invalid-end-") is False
        assert module._is_valid_kebab_case("double--dash") is False

    def test_reserved_names_detection(self):
        """Test detection of reserved names."""
        from skill_fleet.core.modules.validation.structure import ValidateStructureModule

        module = ValidateStructureModule()

        assert module._is_reserved_name("claude") is True
        assert module._is_reserved_name("anthropic") is True
        assert module._is_reserved_name("claude-code") is True
        assert module._is_reserved_name("my-skill") is False


# =============================================================================
# Test Case Generation
# =============================================================================


class TestCaseGeneration:
    """Tests for test case generation module."""

    def test_test_cases_match_trigger_phrases(self, mock_lm):
        """Test that generated test cases match the provided trigger phrases."""
        from skill_fleet.core.modules.validation.test_cases import GenerateTestCasesModule

        module = GenerateTestCasesModule()

        trigger_phrases = ["create react component", "build typescript component"]
        negative_triggers = ["vue component", "angular"]

        result = module.forward(
            skill_description="Create React components with TypeScript",
            trigger_phrases=trigger_phrases,
            negative_triggers=negative_triggers,
            skill_category="document_creation",
        )

        # Verify test cases are generated
        assert "positive_tests" in result
        assert "negative_tests" in result
        assert len(result["positive_tests"]) > 0
        assert len(result["negative_tests"]) > 0

        # Verify trigger coverage is calculated
        assert "trigger_coverage" in result
        assert 0 <= result["trigger_coverage"] <= 1

    def test_diverse_test_cases(self, mock_lm):
        """Test that generated test cases are diverse and relevant."""
        from skill_fleet.core.modules.validation.test_cases import GenerateTestCasesModule

        module = GenerateTestCasesModule()

        result = module.forward(
            skill_description="Create React components with TypeScript",
            trigger_phrases=["react component"],
            negative_triggers=["vue"],
            skill_category="document_creation",
        )

        # Should have different types of tests
        assert "edge_cases" in result
        assert "functional_tests" in result
        assert len(result["edge_cases"]) > 0
        assert len(result["functional_tests"]) > 0

    def test_trigger_coverage_calculation(self):
        """Test the trigger coverage calculation logic."""
        from skill_fleet.core.workflows.skill_creation.validation import ValidationWorkflow

        workflow = ValidationWorkflow()

        # Test full coverage
        positive_tests = ["create react component", "build typescript app"]
        trigger_phrases = ["react", "typescript"]
        coverage = workflow._assess_trigger_coverage(positive_tests, trigger_phrases)
        assert coverage == 1.0

        # Test partial coverage
        positive_tests = ["create react component"]
        trigger_phrases = ["react", "vue", "angular"]
        coverage = workflow._assess_trigger_coverage(positive_tests, trigger_phrases)
        assert coverage == 1 / 3

        # Test no coverage
        positive_tests = ["create react component"]
        trigger_phrases = ["vue", "angular"]
        coverage = workflow._assess_trigger_coverage(positive_tests, trigger_phrases)
        assert coverage == 0.0


# =============================================================================
# Test Quality Validation
# =============================================================================


class TestQualityValidation:
    """Tests for quality validation including size and conciseness."""

    def test_oversized_skill_warning(self, mock_lm):
        """Test that oversized skills get appropriate warnings."""
        from skill_fleet.core.modules.validation.compliance import AssessQualityModule

        module = AssessQualityModule()

        # Create oversized content (>5000 words)
        oversized_content = "word " * 6000

        result = module.forward(
            skill_content=oversized_content,
            plan={"success_criteria": []},
        )

        # Size assessment should flag as too_large
        assert result["size_assessment"] == "too_large"
        assert result["word_count"] > 5000
        assert len(result["size_recommendations"]) > 0

    def test_verbosity_detection(self, mock_lm):
        """Test detection of verbose content."""
        from skill_fleet.core.modules.validation.compliance import AssessQualityModule

        module = AssessQualityModule()

        # Create verbose content with filler phrases
        verbose_content = (
            """
        In order to create a component, it is important to note that you must first
        understand the basics. Due to the fact that React is complex, at this point in time
        you should consider the fact that learning takes time. For the purpose of this guide,
        it should be noted that we will cover the essentials. In the event that you need help,
        please refer to additional resources. It is important to note that practice makes perfect.
        """
            * 10
        )

        result = module.forward(
            skill_content=verbose_content,
            plan={"success_criteria": []},
        )

        # Should detect verbosity
        assert result["verbosity_score"] > 0.0
        assert len(result["conciseness_recommendations"]) > 0

    def test_quality_metrics_present(self, mock_lm):
        """Test that all expected quality metrics are present in results."""
        from skill_fleet.core.modules.validation.compliance import AssessQualityModule

        module = AssessQualityModule()

        result = module.forward(
            skill_content="# Test Skill\n\nSome content here.",
            plan={"success_criteria": ["Test criterion"]},
        )

        # Check all expected fields
        expected_fields = [
            "overall_score",
            "word_count",
            "size_assessment",
            "verbosity_score",
            "size_recommendations",
            "conciseness_recommendations",
        ]

        for field in expected_fields:
            assert field in result, f"Missing field: {field}"


# =============================================================================
# Test Template Compliance
# =============================================================================


class TestTemplateCompliance:
    """Tests for category-specific template compliance."""

    def test_document_creation_template_sections(self):
        """Test that document creation skills have required sections."""
        from skill_fleet.core.modules.generation.templates import (
            get_template_for_category,
        )

        template = get_template_for_category("document_creation")

        assert "sections" in template
        assert "## Output Format" in template["sections"]
        assert "## Style Guidelines" in template["sections"]
        assert "## Examples" in template["sections"]

    def test_workflow_automation_template_sections(self):
        """Test that workflow automation skills have required sections."""
        from skill_fleet.core.modules.generation.templates import get_template_for_category

        template = get_template_for_category("workflow_automation")

        assert "sections" in template
        assert "## Workflow Steps" in template["sections"]
        assert "## Input/Output" in template["sections"]
        assert "## Error Handling" in template["sections"]

    def test_mcp_enhancement_template_sections(self):
        """Test that MCP enhancement skills have required sections."""
        from skill_fleet.core.modules.generation.templates import get_template_for_category

        template = get_template_for_category("mcp_enhancement")

        assert "sections" in template
        assert "## MCP Tools Used" in template["sections"]
        assert "## Tool Sequences" in template["sections"]

    def test_template_validation_function(self):
        """Test the template validation function."""
        from skill_fleet.core.modules.generation.templates import (
            SkillTemplate,
            validate_against_template,
        )

        # Valid content with required sections
        valid_content = """
        ## Output Format
        Some format info
        ## Examples
        Some examples
        """

        template: SkillTemplate = {
            "sections": ["## Output Format", "## Examples"],
            "required_elements": ["examples"],
            "example_skills": [],
        }

        result = validate_against_template(valid_content, template)

        assert "compliance_score" in result
        assert "missing_sections" in result

    def test_unknown_category_defaults(self):
        """Test that unknown categories get default template."""
        from skill_fleet.core.modules.generation.templates import get_template_for_category

        template = get_template_for_category("unknown_category")

        # Should return default/other template
        assert "sections" in template


# =============================================================================
# Test End-to-End Validation Workflow
# =============================================================================


class TestEndToEndValidation:
    """End-to-end tests for the full validation workflow."""

    @pytest.mark.asyncio
    async def test_full_validation_workflow(self, mock_lm, sample_skill_content, sample_plan):
        """Test complete validation workflow execution."""
        from skill_fleet.core.workflows.skill_creation.validation import ValidationWorkflow

        workflow = ValidationWorkflow()

        result = await workflow.execute(
            skill_content=sample_skill_content,
            plan=sample_plan,
            taxonomy_path="technical/frontend/react",
            quality_threshold=0.75,
        )

        # Verify workflow completed
        assert "status" in result
        assert "validation_report" in result

        report = result["validation_report"]

        # Check all validation report fields
        assert "passed" in report
        assert "score" in report
        assert "errors" in report
        assert "warnings" in report
        assert "checks_performed" in report

        # Check new validation fields
        assert "structure_valid" in report
        assert "test_cases" in report
        assert "trigger_coverage" in report
        assert "word_count" in report
        assert "size_assessment" in report
        assert "verbosity_score" in report
        assert "validation_summary" in report

    @pytest.mark.asyncio
    async def test_validation_with_refinement(self, mock_lm):
        """Test validation that triggers content refinement."""
        from skill_fleet.core.workflows.skill_creation.validation import ValidationWorkflow

        workflow = ValidationWorkflow()

        # Low quality content that should trigger refinement
        low_quality_content = """
        ---
        id: test-skill
        name: test-skill
        ---
        # Test
        Some content.
        """

        plan = {
            "skill_name": "test-skill",
            "skill_description": "Test description that is long enough to pass validation checks.",
            "success_criteria": ["Has content"],
            "trigger_phrases": ["test"],
            "negative_triggers": [],
            "skill_category": "document_creation",
        }

        # Mock low quality score to trigger refinement
        with patch.object(
            workflow.quality,
            "aforward",
            return_value={
                "overall_score": 0.6,  # Below threshold
                "weaknesses": ["Too short", "Missing examples"],
                "word_count": 100,
                "size_assessment": "optimal",
                "verbosity_score": 0.2,
                "size_recommendations": [],
                "conciseness_recommendations": [],
            },
        ):
            with patch.object(
                workflow.compliance,
                "aforward",
                return_value={
                    "passed": True,
                    "compliance_score": 0.85,
                    "issues": [],
                    "critical_issues": [],
                    "warnings": [],
                    "auto_fixable": [],
                },
            ):
                result = await workflow.execute(
                    skill_content=low_quality_content,
                    plan=plan,
                    taxonomy_path="test/category",
                    quality_threshold=0.75,
                )

                # Check that refinement was triggered
                assert result["status"] in ["completed", "needs_improvement"]

    @pytest.mark.asyncio
    async def test_hitl_review_checkpoint(self, mock_lm, sample_skill_content, sample_plan):
        """Test that HITL review checkpoint is created when requested."""
        from skill_fleet.core.workflows.skill_creation.validation import ValidationWorkflow

        workflow = ValidationWorkflow()

        result = await workflow.execute(
            skill_content=sample_skill_content,
            plan=sample_plan,
            taxonomy_path="technical/frontend/react",
            enable_hitl_review=True,
        )

        # Should return pending_hitl status
        assert result["status"] == "pending_hitl"
        assert result["hitl_type"] == "review"
        assert "hitl_data" in result
        assert "context" in result

        # Check HITL data contents
        hitl_data = result["hitl_data"]
        assert "skill_content_preview" in hitl_data
        assert "compliance_score" in hitl_data
        assert "quality_score" in hitl_data
        assert "strengths" in hitl_data
        assert "weaknesses" in hitl_data


# =============================================================================
# Test Metrics Collection
# =============================================================================


class TestMetricsCollection:
    """Tests for the metrics collection module."""

    @pytest.mark.asyncio
    async def test_baseline_metrics_collection(self, mock_lm):
        """Test baseline metrics collection."""
        from skill_fleet.core.modules.validation.metrics import MetricsCollectorModule

        module = MetricsCollectorModule()

        result = await module.collect_baseline("Create a React component with TypeScript")

        # Check all expected metrics
        assert "tool_calls" in result
        assert "api_failures" in result
        assert "tokens_consumed" in result
        assert "interaction_turns" in result
        assert "success_rate" in result

        # Validate ranges
        assert result["tool_calls"] >= 0
        assert result["api_failures"] >= 0
        assert result["tokens_consumed"] >= 0
        assert 0 <= result["success_rate"] <= 1

    @pytest.mark.asyncio
    async def test_skill_metrics_collection(self, mock_lm):
        """Test skill-assisted metrics collection."""
        from skill_fleet.core.modules.validation.metrics import MetricsCollectorModule

        module = MetricsCollectorModule()

        skill = {
            "name": "react-component",
            "content": "Guidance for creating React components with TypeScript...",
        }

        result = await module.collect_with_skill("Create a React component with TypeScript", skill)

        # Check all expected metrics
        assert "tool_calls" in result
        assert "api_failures" in result
        assert "tokens_consumed" in result
        assert "interaction_turns" in result
        assert "success_rate" in result

    def test_metrics_comparison(self, mock_lm):
        """Test metrics comparison calculation."""
        from skill_fleet.core.modules.validation.metrics import MetricsCollectorModule

        module = MetricsCollectorModule()

        baseline = {
            "tool_calls": 10,
            "api_failures": 2,
            "tokens_consumed": 5000,
            "interaction_turns": 8,
            "success_rate": 0.6,
        }

        with_skill = {
            "tool_calls": 4,
            "api_failures": 0,
            "tokens_consumed": 2000,
            "interaction_turns": 3,
            "success_rate": 0.95,
        }

        result = module.compare(baseline, with_skill)

        # Check comparison results
        assert result["token_reduction"] == 0.6  # (5000-2000)/5000
        assert result["api_failure_reduction"] == 2
        assert result["interaction_reduction"] == 5
        assert result["success_rate_change"] == 0.35
        assert result["tool_call_reduction"] == 6
        assert result["meets_targets"] is True
        assert len(result["recommendations"]) > 0

    def test_target_achievement_check(self):
        """Test target achievement validation."""
        from skill_fleet.core.modules.validation.metrics import MetricsCollectorModule

        module = MetricsCollectorModule()

        # Test meeting all targets
        baseline = {"tokens_consumed": 1000, "success_rate": 0.5}
        with_skill = {"tokens_consumed": 400, "success_rate": 0.95, "api_failures": 0}

        targets = module._get_target_details(baseline, with_skill)

        assert targets["trigger_rate"]["met"] is True  # 0.95 >= 0.9
        assert targets["token_reduction"]["met"] is True  # 0.6 >= 0.5
        assert targets["api_failures"]["met"] is True  # 0 == 0

        # Test failing targets
        baseline = {"tokens_consumed": 1000, "success_rate": 0.5}
        with_skill = {"tokens_consumed": 800, "success_rate": 0.85, "api_failures": 1}

        targets = module._get_target_details(baseline, with_skill)

        assert targets["trigger_rate"]["met"] is False  # 0.85 < 0.9
        assert targets["token_reduction"]["met"] is False  # 0.2 < 0.5
        assert targets["api_failures"]["met"] is False  # 1 != 0


# =============================================================================
# Main Test Runner
# =============================================================================


async def main():
    """Run all integration tests."""
    print("\n" + "=" * 70)
    print("ENHANCED VALIDATION PIPELINE INTEGRATION TESTS")
    print("=" * 70)

    # Setup mock LM
    mock_lm = MockLM()
    dspy.configure(lm=mock_lm)

    test_classes = [
        TestStructureValidation(),
        TestCaseGeneration(),
        TestQualityValidation(),
        TestTemplateCompliance(),
    ]

    passed = 0
    failed = 0

    # Run synchronous tests
    for test_class in test_classes:
        class_name = test_class.__class__.__name__
        print(f"\n📦 {class_name}")
        print("-" * 40)

        for method_name in dir(test_class):
            if method_name.startswith("test_"):
                try:
                    method = getattr(test_class, method_name)
                    # Check if async
                    if asyncio.iscoroutinefunction(method):
                        asyncio.run(method(mock_lm))
                    else:
                        method(mock_lm)
                    print(f"  ✅ {method_name}")
                    passed += 1
                except Exception as e:
                    print(f"  ❌ {method_name}: {e}")
                    failed += 1

    # Run async tests
    async_test_classes = [TestEndToEndValidation(), TestMetricsCollection()]

    for test_class in async_test_classes:
        class_name = test_class.__class__.__name__
        print(f"\n📦 {class_name}")
        print("-" * 40)

        for method_name in dir(test_class):
            if method_name.startswith("test_"):
                try:
                    method = getattr(test_class, method_name)
                    await method(
                        mock_lm, None, None
                    ) if "full" in method_name or "hitl" in method_name else await method(mock_lm)
                    print(f"  ✅ {method_name}")
                    passed += 1
                except Exception as e:
                    print(f"  ❌ {method_name}: {e}")
                    failed += 1

    # Summary
    print("\n" + "=" * 70)
    print("TEST SUMMARY")
    print("=" * 70)
    print(f"\n✅ Passed: {passed}")
    print(f"❌ Failed: {failed}")
    print(f"📊 Total: {passed + failed}")

    if failed == 0:
        print("\n🎉 All tests passed!")
    else:
        print(f"\n⚠️  {failed} test(s) failed")

    return failed == 0


if __name__ == "__main__":
    success = asyncio.run(main())
    exit(0 if success else 1)
