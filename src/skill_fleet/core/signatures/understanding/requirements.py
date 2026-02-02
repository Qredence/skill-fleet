"""
DSPy signature for gathering requirements from task descriptions.

This signature extracts structured requirements including domain, topics,
constraints, and ambiguities that may require HITL clarification.

Also generates validation-oriented outputs to ensure skill quality and
compliance with Anthropic's skill building guidelines.
"""

from typing import Literal

import dspy

# Type definitions for constrained outputs
Domain = Literal["technical", "cognitive", "domain_knowledge", "tool", "meta"]
TargetLevel = Literal["beginner", "intermediate", "advanced", "expert"]
SkillCategory = Literal[
    "document_creation", "workflow_automation", "mcp_enhancement", "analysis", "other"
]


class GatherRequirements(dspy.Signature):
    """
    Extract structured requirements from user task description.

    Identify domain, skill level, topics, and ambiguities for HITL clarification.
    Generate validation-oriented outputs for skill name, trigger phrases, and
    category detection to ensure compliance with skill building best practices.
    Be specific about what's unclear vs. what can be inferred.
    """

    # Inputs
    task_description: str = dspy.InputField(
        desc="User's task description, may include clarifications from previous rounds"
    )
    user_context: str = dspy.InputField(
        desc="JSON user context: user_id, existing_skills (list of IDs), preferences (dict)",
        default="{}",
    )

    # Outputs
    domain: Domain = dspy.OutputField(
        desc="Primary domain based on skill content: technical (code/tools), cognitive (thinking patterns), "
        "domain_knowledge (specific field), tool (specific software), or meta (about skills themselves)"
    )
    category: str = dspy.OutputField(
        desc="Specific category within domain (e.g., 'python', 'devops', 'web', 'testing'). "
        "Use kebab-case, match existing taxonomy categories when possible. Single word preferred."
    )
    target_level: TargetLevel = dspy.OutputField(
        desc="Target expertise level: beginner (assumes no prior knowledge), intermediate (assumes basics), "
        "advanced (assumes strong foundation), expert (edge cases and optimizations)"
    )
    topics: list[str] = dspy.OutputField(
        desc="3-7 specific topics to cover. Be concrete (not 'basics' but 'async/await syntax'). "
        "Order by importance. Each topic should map to a skill section or pattern."
    )
    constraints: list[str] = dspy.OutputField(
        desc="Technical constraints and preferences (e.g., 'Python 3.12+', 'production patterns only', "
        "'no deprecated features'). Empty list [] if none detected. Max 5 constraints."
    )
    ambiguities: list[str] = dspy.OutputField(
        desc="Unclear aspects requiring HITL clarification (e.g., 'Unclear if user wants sync or async examples'). "
        "Be specific about what's ambiguous. Empty list [] if task is clear. Max 3 ambiguities."
    )

    description: str = dspy.OutputField(
        desc="CSO-optimized description: include a 'Use when...' clause and 1-2 trigger conditions. "
        "Keep concise (1-2 sentences)."
    )

    # Validation-oriented outputs (NEW)
    suggested_skill_name: str = dspy.OutputField(
        desc="Suggested skill name in kebab-case (lowercase letters, numbers, hyphens only). "
        "Should be 3-5 words, descriptive and unique. Example: 'react-component-generator'"
    )

    trigger_phrases: list[str] = dspy.OutputField(
        desc="5-7 specific user phrases that SHOULD trigger this skill. "
        "Examples: 'create React component', 'analyze CSV data', 'generate API docs'. "
        "These will be incorporated into the description's 'Use when' clause."
    )

    negative_triggers: list[str] = dspy.OutputField(
        desc="3-5 contexts where skill should NOT trigger. "
        "Examples: 'simple queries', 'general questions', 'unrelated topics'. "
        "Helps prevent over-triggering."
    )

    skill_category: SkillCategory = dspy.OutputField(
        desc="Category determines template and validation rules: "
        "document_creation (for creating documents/assets), "
        "workflow_automation (for multi-step processes), "
        "mcp_enhancement (for MCP-guided workflows), "
        "analysis (for data/code analysis), "
        "other (doesn't fit above categories)"
    )

    requires_mcp: bool = dspy.OutputField(
        desc="Whether this skill requires MCP (Model Context Protocol) server integration. "
        "True if skill needs to call external tools/services via MCP."
    )

    suggested_mcp_server: str = dspy.OutputField(
        desc="If requires_mcp is True, suggest appropriate MCP server name. "
        "Examples: 'linear', 'notion', 'github', 'slack'. "
        "Empty string if requires_mcp is False."
    )
    reasoning: dspy.Reasoning = dspy.OutputField(desc="Reasoning process for requirements analysis")
