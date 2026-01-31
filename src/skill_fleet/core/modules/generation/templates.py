"""
Category-specific skill templates.

This module provides template structures for different skill categories
to ensure generated skills follow best practices for their intended use case.
"""

from __future__ import annotations

from typing import TypedDict


class SkillTemplate(TypedDict):
    """Type definition for skill templates."""

    sections: list[str]
    required_elements: list[str]
    example_skills: list[str]


# Skill templates by category
SKILL_TEMPLATES: dict[str, SkillTemplate] = {
    "document_creation": {
        "sections": [
            "## Output Format",
            "## Style Guidelines",
            "## Quality Checklist",
            "## Examples",
        ],
        "required_elements": ["template", "style_guide", "examples"],
        "example_skills": ["frontend-design", "docx", "pptx", "xlsx"],
    },
    "workflow_automation": {
        "sections": [
            "## Workflow Steps",
            "## Input/Output",
            "## Error Handling",
            "## Validation Gates",
        ],
        "required_elements": ["step_by_step", "validation", "error_handling"],
        "example_skills": ["skill-creator", "onboarding", "sprint-planning"],
    },
    "mcp_enhancement": {
        "sections": [
            "## MCP Tools Used",
            "## Tool Sequences",
            "## Error Recovery",
            "## Prerequisites",
        ],
        "required_elements": ["mcp_tools", "patterns", "prerequisites"],
        "example_skills": ["sentry-code-review", "linear-workflow", "notion-setup"],
    },
    "analysis": {
        "sections": [
            "## Analysis Method",
            "## Input Requirements",
            "## Output Format",
            "## Interpretation Guidelines",
        ],
        "required_elements": ["method", "input_requirements", "output_format"],
        "example_skills": ["code-review", "data-analysis", "security-audit"],
    },
}

# Default template for unknown categories
DEFAULT_TEMPLATE: SkillTemplate = {
    "sections": [
        "## Instructions",
        "## Examples",
        "## Troubleshooting",
    ],
    "required_elements": ["instructions", "examples"],
    "example_skills": [],
}


def get_template_for_category(category: str) -> SkillTemplate:
    """
    Get template structure for skill category.

    Args:
        category: Skill category (document_creation, workflow_automation,
                 mcp_enhancement, analysis, or other)

    Returns:
        Template dict with sections, required_elements, and example_skills

    Example:
        >>> template = get_template_for_category("document_creation")
        >>> template["sections"]
        ['## Output Format', '## Style Guidelines', '## Quality Checklist', '## Examples']

    """
    return SKILL_TEMPLATES.get(category, DEFAULT_TEMPLATE)


def validate_against_template(content: str, template: SkillTemplate) -> dict:
    """
    Validate skill content against template requirements.

    Args:
        content: Full SKILL.md content
        template: Template to validate against

    Returns:
        Validation report with compliance score and issues

    """
    issues = []
    found_sections = []

    for section in template["sections"]:
        if section in content:
            found_sections.append(section)
        else:
            issues.append(f"Missing required section: {section}")

    # Check for required elements (basic heuristic)
    for element in template["required_elements"]:
        element_found = _check_element_in_content(content, element)
        if not element_found:
            issues.append(f"Missing required element: {element}")

    compliance_score = len(found_sections) / len(template["sections"])

    return {
        "compliance_score": compliance_score,
        "found_sections": found_sections,
        "missing_sections": [s for s in template["sections"] if s not in content],
        "issues": issues,
        "compliant": compliance_score >= 0.75 and len(issues) <= 2,
    }


def _check_element_in_content(content: str, element: str) -> bool:
    """Check if an element is present in content (heuristic)."""
    element_variations = {
        "template": ["template", "boilerplate", "starter"],
        "style_guide": ["style", "guideline", "formatting", "convention"],
        "examples": ["example", "sample", "demo"],
        "step_by_step": ["step", "phase", "stage"],
        "validation": ["validate", "check", "verify", "quality"],
        "error_handling": ["error", "exception", "failure", "troubleshoot"],
        "mcp_tools": ["mcp", "tool", "api", "server"],
        "patterns": ["pattern", "sequence", "flow", "workflow"],
        "prerequisites": ["prerequisite", "requirement", "setup", "install"],
        "method": ["method", "approach", "technique", "process"],
        "input_requirements": ["input", "requirement", "data needed"],
        "output_format": ["output", "format", "result", "deliverable"],
        "instructions": ["instruction", "guide", "how to", "steps"],
    }

    variations = element_variations.get(element, [element])
    content_lower = content.lower()

    return any(v in content_lower for v in variations)


def get_required_sections(category: str) -> list[str]:
    """
    Get required sections for a category.

    Args:
        category: Skill category

    Returns:
        List of required section headers

    """
    template = get_template_for_category(category)
    return template["sections"]


def get_example_skills(category: str) -> list[str]:
    """
    Get example skills for a category.

    Args:
        category: Skill category

    Returns:
        List of example skill names

    """
    template = get_template_for_category(category)
    return template["example_skills"]
