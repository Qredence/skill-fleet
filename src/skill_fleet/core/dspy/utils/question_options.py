"""Smart option generation utility for clarifying questions.

This module provides intelligent option generation based on question text
and task context to ensure multi-select behavior with sensible defaults.
"""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    pass


def generate_smart_options(
    question_text: str, task_context: str = ""
) -> tuple[list[str], str | None]:
    """Generate sensible multi-select options for a question.

    Args:
        question_text: The question to generate options for
        task_context: Task description for domain inference

    Returns:
        (options_list, refined_question) where refined_question may be None

    Generates domain-specific default options:
    - Programming: ["Python", "TypeScript", "JavaScript", "Go", "Rust", "Other"]
    - Project state: ["New/greenfield", "Existing/legacy", "Refactoring", "Migration", "Other"]
    - Team size: ["Solo developer", "Small team (2-10)", "Medium team (10-50)", "Large team (50+)", "Other"]
    - Priority: ["High priority/urgent", "Medium priority", "Low priority/nice to have", "Other"]
    - Scope: ["Single file/function", "Module/package", "Full project", "Multiple projects", "Other"]
    - Experience: ["Beginner (learning)", "Intermediate (some experience)", "Advanced (expert)", "Other"]
    - CI/CD: ["GitHub Actions", "GitLab CI", "CircleCI", "Jenkins", "Other"]
    """
    question_lower = question_text.lower()
    options = []
    refined_question = None

    # Domain-specific option generation
    if any(
        word in question_lower
        for word in ["language", "python", "typescript", "javascript", "go", "rust"]
    ):
        options = ["Python", "TypeScript", "JavaScript/Node", "Go", "Rust", "Other"]
        refined_question = "Which programming language(s) are you working with?"

    elif any(
        word in question_lower for word in ["project", "codebase", "existing", "new", "legacy"]
    ):
        options = [
            "New/greenfield project",
            "Existing/legacy codebase",
            "Refactoring existing code",
            "Migration from another tool",
            "Other",
        ]
        refined_question = "What is the current state of your project?"

    elif any(word in question_lower for word in ["team", "collaborator", "organization"]):
        options = [
            "Solo developer",
            "Small team (2-10 people)",
            "Medium team (10-50 people)",
            "Large team (50+ people)",
            "Other",
        ]

    elif any(word in question_lower for word in ["priority", "urgent", "deadline"]):
        options = ["High priority/urgent", "Medium priority", "Low priority/nice to have", "Other"]

    elif any(word in question_lower for word in ["scope", "coverage", "files", "module"]):
        options = [
            "Single file or function",
            "Module or package",
            "Full project",
            "Multiple projects",
            "Other",
        ]

    elif any(word in question_lower for word in ["experience", "skill level", "familiarity"]):
        options = [
            "Beginner (just learning)",
            "Intermediate (some experience)",
            "Advanced (expert)",
            "Other",
        ]

    elif any(word in question_lower for word in ["ci", "cd", "pipeline", "deployment"]):
        options = ["GitHub Actions", "GitLab CI/CD", "CircleCI", "Jenkins", "Travis CI", "Other"]

    # Generic fallback for unknown domains
    if not options:
        options = ["Yes", "No", "Not sure", "Other"]

    # Ensure options are 2-5 in length
    if len(options) > 5:
        options = options[:4] + ["Other"]
    elif len(options) < 2:
        options = ["Yes", "No", "Other"]

    return options, refined_question
