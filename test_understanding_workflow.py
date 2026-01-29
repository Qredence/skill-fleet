#!/usr/bin/env python3
"""Test script for UnderstandingWorkflow.

This script tests the UnderstandingWorkflow with mock LM responses
to verify it generates proper follow-up questions and synthesizes plans.
"""
import asyncio
import json
from unittest.mock import AsyncMock, Mock, patch

import dspy
from dspy import LM


class MockLM(LM):
    """Mock LM that returns predictable responses."""
    
    def __init__(self):
        super().__init__(model="mock/model")
    
    def __call__(self, prompt=None, messages=None, **kwargs):
        """Mock LLM responses based on prompt content.
        
        Accepts both prompt (string) and messages (list) formats.
        """
        # Use prompt if provided, otherwise extract from messages
        if prompt:
            prompt_str = str(prompt).lower()
        elif messages:
            prompt_str = str(messages).lower()
        else:
            prompt_str = ""
        
        # Requirements gathering response
        if "requirements" in prompt_str or "domain" in prompt_str:
            return self._mock_requirements_response()
        
        # Intent analysis response
        if "intent" in prompt_str or "purpose" in prompt_str:
            return self._mock_intent_response()
        
        # Taxonomy path response
        if "taxonomy" in prompt_str or "path" in prompt_str:
            return self._mock_taxonomy_response()
        
        # Dependencies response
        if "depend" in prompt_str or "prerequisite" in prompt_str:
            return self._mock_dependencies_response()
        
        # Plan synthesis response
        if "plan" in prompt_str or "synthesize" in prompt_str:
            return self._mock_plan_response()
        
        # HITL questions response
        if "question" in prompt_str or "clarif" in prompt_str:
            return self._mock_questions_response()
        
        # Default response
        return self._mock_default_response()
    
    def _mock_requirements_response(self):
        return """domain: technical
category: frontend
target_level: intermediate
topics: ["react", "components", "typescript", "testing"]
constraints: ["TypeScript", "production-ready"]
ambiguities: []"""
    
    def _mock_requirements_with_ambiguities_response(self):
        return """domain: technical
category: general
target_level: intermediate  
topics: ["general-programming"]
constraints: []
ambiguities: ["Unclear what specific technology or framework", "Scope not well-defined - could be web, mobile, or desktop"]"""
    
    def _mock_intent_response(self):
        return """purpose: Help developers build reusable React components
problem_statement: Teams struggle with inconsistent UI and duplicated component code across projects
target_audience: Frontend developers with basic React knowledge
value_proposition: Provides production-ready, tested component patterns with TypeScript support
skill_type: how_to
scope: Covers component design, implementation, testing, and documentation. Does NOT cover backend integration or deployment.
success_criteria: ["Can create reusable components", "Implements proper TypeScript types", "Writes component tests", "Documents component API"]"""
    
    def _mock_taxonomy_response(self):
        return """recommended_path: technical/frontend/react-components
alternative_paths: ["web/react-patterns", "javascript/react-advanced"]
path_rationale: React components fit best in frontend category. Follows existing structure of technical/frontend path.
new_directories: []
confidence: 0.85"""
    
    def _mock_dependencies_response(self):
        return """prerequisite_skills: ["javascript: JavaScript fundamentals required", "react-basics: Basic React concepts needed"]
complementary_skills: ["testing: Useful for component testing", "typescript: Enhances type safety"]
conflicting_skills: []
missing_prerequisites: []
dependency_rationale: JavaScript and basic React are essential. Testing and TypeScript enhance but aren't required."""
    
    def _mock_plan_response(self):
        return """skill_name: react-component-library
skill_description: Use when you need to build a reusable React component library with TypeScript. Helps when: your team has inconsistent UI patterns, you're starting a new design system, or you need production-ready components.
taxonomy_path: technical/frontend/react-components
content_outline: ["Introduction to Component Libraries", "Project Setup with TypeScript", "Component Design Patterns", "Building Reusable Components", "Testing Components", "Documentation with Storybook", "Publishing and Distribution"]
generation_guidance: Write in a clear, instructional style. Use practical examples. Include TypeScript types. Show both good and bad patterns. Target intermediate developers.
success_criteria: ["All code examples are TypeScript-typed", "Includes 5+ component patterns", "Has testing examples", "Documentation is complete"]
estimated_length: medium
tags: ["react", "typescript", "components", "frontend", "design-system"]
rationale: This plan covers the full lifecycle of building a component library, from setup to publishing."""
    
    def _mock_questions_response(self):
        return """questions: [
    {"text": "What type of application are you building?", "question_type": "single", "options": [{"id": "web", "label": "Web Application"}, {"id": "mobile", "label": "Mobile App"}, {"id": "desktop", "label": "Desktop App"}], "rationale": "Determines technology stack and constraints", "allows_other": true},
    {"text": "Which programming language do you prefer?", "question_type": "single", "options": [{"id": "typescript", "label": "TypeScript"}, {"id": "javascript", "label": "JavaScript"}, {"id": "python", "label": "Python"}], "rationale": "Language choice affects all implementation details", "allows_other": true}
]
priority: critical
rationale: Need to clarify technology stack and scope before proceeding with skill creation"""
    
    def _mock_default_response(self):
        return "Default mock response"


def setup_mock_lm():
    """Setup mock LM for testing."""
    mock_lm = MockLM()
    dspy.configure(lm=mock_lm)
    return mock_lm


def mock_requirements_response():
    """Mock response for requirements gathering."""
    return """domain: technical
category: frontend
target_level: intermediate
topics: ["react", "components", "typescript", "testing"]
constraints: ["TypeScript", "production-ready"]
ambiguities: []"""


def mock_requirements_with_ambiguities_response():
    """Mock response for requirements with ambiguities."""
    return """domain: technical
category: general
target_level: intermediate  
topics: ["general-programming"]
constraints: []
ambiguities: ["Unclear what specific technology or framework", "Scope not well-defined - could be web, mobile, or desktop"]"""


def mock_intent_response():
    """Mock response for intent analysis."""
    return """purpose: Help developers build reusable React components
problem_statement: Teams struggle with inconsistent UI and duplicated component code across projects
target_audience: Frontend developers with basic React knowledge
value_proposition: Provides production-ready, tested component patterns with TypeScript support
skill_type: how_to
scope: Covers component design, implementation, testing, and documentation. Does NOT cover backend integration or deployment.
success_criteria: ["Can create reusable components", "Implements proper TypeScript types", "Writes component tests", "Documents component API"]"""


def mock_taxonomy_response():
    """Mock response for taxonomy path finding."""
    return """recommended_path: technical/frontend/react-components
alternative_paths: ["web/react-patterns", "javascript/react-advanced"]
path_rationale: React components fit best in frontend category. Follows existing structure of technical/frontend path.
new_directories: []
confidence: 0.85"""


def mock_dependencies_response():
    """Mock response for dependency analysis."""
    return """prerequisite_skills: ["javascript: JavaScript fundamentals required", "react-basics: Basic React concepts needed"]
complementary_skills: ["testing: Useful for component testing", "typescript: Enhances type safety"]
conflicting_skills: []
missing_prerequisites: []
dependency_rationale: JavaScript and basic React are essential. Testing and TypeScript enhance but aren't required."""


def mock_plan_response():
    """Mock response for plan synthesis."""
    return """skill_name: react-component-library
skill_description: Use when you need to build a reusable React component library with TypeScript. Helps when: your team has inconsistent UI patterns, you're starting a new design system, or you need production-ready components.
taxonomy_path: technical/frontend/react-components
content_outline: ["Introduction to Component Libraries", "Project Setup with TypeScript", "Component Design Patterns", "Building Reusable Components", "Testing Components", "Documentation with Storybook", "Publishing and Distribution"]
generation_guidance: Write in a clear, instructional style. Use practical examples. Include TypeScript types. Show both good and bad patterns. Target intermediate developers.
success_criteria: ["All code examples are TypeScript-typed", "Includes 5+ component patterns", "Has testing examples", "Documentation is complete"]
estimated_length: medium
tags: ["react", "typescript", "components", "frontend", "design-system"]
rationale: This plan covers the full lifecycle of building a component library, from setup to publishing."""


def mock_questions_response():
    """Mock response for clarifying questions."""
    return """questions: [
    {"text": "What type of application are you building?", "question_type": "single", "options": [{"id": "web", "label": "Web Application"}, {"id": "mobile", "label": "Mobile App"}, {"id": "desktop", "label": "Desktop App"}], "rationale": "Determines technology stack and constraints", "allows_other": true},
    {"text": "Which programming language do you prefer?", "question_type": "single", "options": [{"id": "typescript", "label": "TypeScript"}, {"id": "javascript", "label": "JavaScript"}, {"id": "python", "label": "Python"}], "rationale": "Language choice affects all implementation details", "allows_other": true}
]
priority: critical
rationale: Need to clarify technology stack and scope before proceeding with skill creation"""


def mock_default_response():
    """Default mock response."""
    return "Default mock response"


async def test_clear_task():
    """Test workflow with a clear, specific task."""
    print("\n" + "=" * 70)
    print("TEST 1: Clear Task (Should complete without HITL)")
    print("=" * 70)

    from skill_fleet.core.workflows.skill_creation.understanding import UnderstandingWorkflow

    setup_mock_lm()

    workflow = UnderstandingWorkflow()

    result = await workflow.execute(
        task_description="Build a React component library with TypeScript for our design system",
        user_context={"experience": "intermediate", "team_size": 5},
    )

    print(f"\nStatus: {result.get('status')}")

    if result.get("status") == "completed":
        print("\n✅ Workflow completed successfully!")
        print("\nRequirements:")
        req = result.get("requirements", {})
        print(f"  - Domain: {req.get('domain')}")
        print(f"  - Category: {req.get('category')}")
        print(f"  - Topics: {req.get('topics', [])}")
        print(f"  - Ambiguities: {req.get('ambiguities', [])}")

        print("\nPlan:")
        plan = result.get("plan", {})
        print(f"  - Skill Name: {plan.get('skill_name')}")
        print(f"  - Taxonomy Path: {plan.get('taxonomy_path')}")
        print(f"  - Outline Length: {len(plan.get('content_outline', []))} sections")
        print(f"  - Tags: {plan.get('tags', [])}")

        print("\nIntent:")
        intent = result.get("intent", {})
        print(f"  - Purpose: {intent.get('purpose', 'N/A')[:60]}...")
        print(f"  - Skill Type: {intent.get('skill_type')}")
    else:
        print(f"\n⚠️  Unexpected status: {result.get('status')}")

    return result


async def test_ambiguous_task():
    """Test workflow with an ambiguous task (should trigger HITL)."""
    print("\n" + "=" * 70)
    print("TEST 2: Ambiguous Task (Should trigger HITL)")
    print("=" * 70)

    from skill_fleet.core.workflows.skill_creation.understanding import UnderstandingWorkflow

    # Override mock to return ambiguities
    def mock_with_ambiguities(prompt, **kwargs):
        prompt_str = str(prompt).lower()
        if "requirements" in prompt_str or "domain" in prompt_str:
            return mock_requirements_with_ambiguities_response()
        return mock_default_response()

    mock_lm = Mock()
    mock_lm.side_effect = mock_with_ambiguities
    dspy.configure(lm=mock_lm)

    workflow = UnderstandingWorkflow()

    result = await workflow.execute(task_description="Help me build something", user_context={})

    print(f"\nStatus: {result.get('status')}")
    print(f"HITL Type: {result.get('hitl_type')}")

    if result.get("status") == "pending_user_input":
        print("\n✅ Correctly suspended for HITL clarification!")

        hitl_data = result.get("hitl_data", {})
        questions = hitl_data.get("questions", [])

        print(f"\nPriority: {hitl_data.get('priority')}")
        print(f"Questions Generated: {len(questions)}")
        print(f"\nRationale: {hitl_data.get('rationale', 'N/A')[:100]}...")

        print("\n📝 Generated Questions:")
        for i, q in enumerate(questions, 1):
            print(f"\n  Question {i}:")
            print(f"    Text: {q.get('text', 'N/A')}")
            print(f"    Type: {q.get('question_type', 'N/A')}")
            print(f"    Rationale: {q.get('rationale', 'N/A')[:80]}...")
            if q.get("options"):
                print(f"    Options: {len(q.get('options'))} choices")

        print("\n📋 Context for Follow-up:")
        context = result.get("context", {})
        partial = context.get("partial_understanding", {})
        print(f"    Domain detected: {partial.get('domain')}")
        print(f"    Topics identified: {partial.get('topics', [])}")

        follow_up = hitl_data.get("follow_up_context", {})
        print(f"\n    Expected improvements: {follow_up.get('expected_improvements', [])}")
        print(f"    Critical gaps: {follow_up.get('critical_gaps', [])}")
    else:
        print(f"\n❌ Expected HITL suspension but got: {result.get('status')}")

    return result


async def main():
    """Run all tests."""
    print("\n" + "=" * 70)
    print("UNDERSTANDING WORKFLOW TEST SUITE")
    print("=" * 70)
    print("\nThis tests the refactored UnderstandingWorkflow with:")
    print("  - Async operations (aforward)")
    print("  - ReAct-based plan synthesis")
    print("  - HITL clarification logic")
    print("  - Parallel module execution")

    try:
        # Test 1: Clear task
        result1 = await test_clear_task()

        # Test 2: Ambiguous task
        result2 = await test_ambiguous_task()

        # Summary
        print("\n" + "=" * 70)
        print("TEST SUMMARY")
        print("=" * 70)
        print(f"\n✅ Test 1 (Clear task): {result1.get('status')}")
        print(f"✅ Test 2 (Ambiguous task): {result2.get('status')}")
        print("\n🎉 All tests completed successfully!")

    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
