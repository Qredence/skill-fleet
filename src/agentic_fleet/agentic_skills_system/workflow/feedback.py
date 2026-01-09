"""Human feedback handlers for skill approval workflow."""

import json
import logging
from abc import ABC, abstractmethod
from datetime import datetime

logger = logging.getLogger(__name__)


class FeedbackHandler(ABC):
    """Abstract base class for feedback handlers."""

    @abstractmethod
    def get_feedback(self, packaging_manifest: str, validation_report: dict) -> str:
        """Get human feedback on packaged skill.

        Returns:
            JSON string with feedback structure:
            {
                "status": "approved" | "needs_revision" | "rejected",
                "comments": "...",
                "reviewer": "...",
                "timestamp": "..."
            }
        """
        pass


class AutoApprovalHandler(FeedbackHandler):
    """Automatic approval based on validation results."""

    def get_feedback(self, packaging_manifest: str, validation_report: dict) -> str:
        """Auto-approve if validation passed, otherwise request revision."""

        passed_statuses = ["passed", "validated", "approved", "success"]
        is_passed = (
            validation_report.get("passed", False)
            or validation_report.get("status", "").lower() in passed_statuses
        )

        if is_passed:
            return json.dumps(
                {
                    "status": "approved",
                    "comments": "Validation passed - auto-approved",
                    "reviewer": "system",
                    "timestamp": datetime.now().isoformat(),
                }
            )
        else:
            errors = validation_report.get("errors", [])
            return json.dumps(
                {
                    "status": "needs_revision",
                    "comments": f"Validation errors: {', '.join(errors[:3]) if errors else 'Unknown validation error'}",
                    "suggested_changes": errors,
                    "reviewer": "system",
                    "timestamp": datetime.now().isoformat(),
                }
            )


class CLIFeedbackHandler(FeedbackHandler):
    """Interactive CLI feedback collection."""

    def get_feedback(self, packaging_manifest: str, validation_report: dict) -> str:
        """Collect feedback via command-line prompts."""

        from rich.console import Console
        from rich.prompt import Prompt

        console = Console()

        # Display validation results
        console.print("\n[bold cyan]Skill Review[/bold cyan]")

        validation_status = "✓ PASSED" if validation_report.get("passed") else "✗ FAILED"
        console.print(f"Validation: {validation_status}")
        console.print(f"Quality Score: {validation_report.get('quality_score', 0):.2f}")

        if validation_report.get("warnings"):
            console.print("\n[yellow]Warnings:[/yellow]")
            for warning in validation_report["warnings"][:5]:
                console.print(f"  ⚠ {warning}")

        if validation_report.get("errors"):
            console.print("\n[red]Errors:[/red]")
            for error in validation_report["errors"][:5]:
                console.print(f"  ✗ {error}")

        # Get decision
        console.print("\n[bold]Review Decision:[/bold]")
        console.print("1. Approve")
        console.print("2. Request Revision")
        console.print("3. Reject")

        choice = Prompt.ask("Choose", choices=["1", "2", "3"], default="1")

        status_map = {"1": "approved", "2": "needs_revision", "3": "rejected"}
        status = status_map[choice]

        comments = Prompt.ask("Comments (optional)", default="")
        reviewer = Prompt.ask("Reviewer name", default="human")

        return json.dumps(
            {
                "status": status,
                "comments": comments,
                "reviewer": reviewer,
                "timestamp": datetime.utcnow().isoformat(),
            }
        )


class InteractiveHITLHandler(FeedbackHandler):
    """Interactive HITL handler with multi-choice clarifying questions.

    Implements a real human-in-the-loop workflow with:
    - Minimum 1 round of clarifying questions before approval
    - Maximum 4 rounds of interaction
    - Multi-choice questions for structured feedback
    - Progressive refinement based on user answers
    """

    def __init__(self, min_rounds: int = 1, max_rounds: int = 4):
        self.min_rounds = max(1, min(min_rounds, 4))
        self.max_rounds = max(self.min_rounds, min(max_rounds, 4))
        self.current_round = 0
        self.session_history: list[dict] = []

    def get_feedback(self, packaging_manifest: str, validation_report: dict) -> str:
        """Collect feedback via interactive multi-choice questions."""
        from rich.console import Console
        from rich.panel import Panel
        from rich.prompt import Prompt
        from rich.table import Table

        console = Console()
        self.current_round += 1

        # Parse manifest if it's a string
        manifest = packaging_manifest
        if isinstance(packaging_manifest, str):
            try:
                manifest = json.loads(packaging_manifest)
            except json.JSONDecodeError:
                manifest = {"raw": packaging_manifest}

        # Display current skill summary
        console.print()
        console.print(
            Panel(
                f"[bold]Skill Review - Round {self.current_round}/{self.max_rounds}[/bold]",
                style="cyan",
            )
        )

        # Show skill info
        skill_name = manifest.get("name", "Unknown")
        skill_id = manifest.get("skill_id", "Unknown")
        version = manifest.get("version", "1.0.0")

        info_table = Table(show_header=False, box=None)
        info_table.add_column("Field", style="bold")
        info_table.add_column("Value")
        info_table.add_row("Name", skill_name)
        info_table.add_row("Skill ID", skill_id)
        info_table.add_row("Version", version)
        console.print(info_table)

        # Show validation status
        validation_status = "✓ PASSED" if validation_report.get("passed") else "✗ FAILED"
        quality_score = validation_report.get("quality_score", 0)
        console.print(f"\n[bold]Validation:[/bold] {validation_status}")
        console.print(f"[bold]Quality Score:[/bold] {quality_score:.2f}")

        if validation_report.get("warnings"):
            console.print("\n[yellow]Warnings:[/yellow]")
            for warning in validation_report["warnings"][:3]:
                console.print(f"  ⚠ {warning}")

        if validation_report.get("errors"):
            console.print("\n[red]Errors:[/red]")
            for error in validation_report["errors"][:3]:
                console.print(f"  ✗ {error}")

        # Generate clarifying questions based on current round
        questions = self._generate_questions(manifest, validation_report, self.current_round)

        # Collect answers
        answers = {}
        console.print("\n[bold cyan]Please answer the following questions:[/bold cyan]\n")

        for i, question in enumerate(questions, 1):
            console.print(f"[bold]{i}. {question['question']}[/bold]")
            if question.get("context"):
                console.print(f"   [dim]{question['context']}[/dim]")

            if question.get("options"):
                # Multi-choice question
                for opt in question["options"]:
                    console.print(f"   [{opt['id']}] {opt['label']}")
                    if opt.get("description"):
                        console.print(f"       [dim]{opt['description']}[/dim]")

                valid_choices = [opt["id"] for opt in question["options"]]
                if question.get("allows_multiple"):
                    console.print(
                        "   [dim](Enter multiple choices separated by comma, e.g., a,b)[/dim]"
                    )
                    choice = Prompt.ask("   Your choice(s)", default=valid_choices[0])
                    answers[question["id"]] = [c.strip() for c in choice.split(",")]
                else:
                    choice = Prompt.ask(
                        "   Your choice", choices=valid_choices, default=valid_choices[0]
                    )
                    answers[question["id"]] = choice
            else:
                # Free-form question
                answer = Prompt.ask("   Your answer", default="")
                answers[question["id"]] = answer

            console.print()

        # Store in session history
        self.session_history.append(
            {
                "round": self.current_round,
                "questions": questions,
                "answers": answers,
            }
        )

        # Determine if we can approve or need more rounds
        can_approve = self.current_round >= self.min_rounds

        if can_approve:
            console.print("\n[bold]Review Decision:[/bold]")
            console.print("1. [green]Approve[/green] - Skill meets requirements")
            console.print("2. [yellow]Request Revision[/yellow] - Need changes based on feedback")
            console.print("3. [red]Reject[/red] - Skill does not meet requirements")
            if self.current_round < self.max_rounds:
                console.print("4. [cyan]Continue Review[/cyan] - Ask more clarifying questions")

            valid_choices = ["1", "2", "3"]
            if self.current_round < self.max_rounds:
                valid_choices.append("4")

            choice = Prompt.ask("Choose", choices=valid_choices, default="1")

            status_map = {
                "1": "approved",
                "2": "needs_revision",
                "3": "rejected",
                "4": "continue",
            }
            status = status_map[choice]

            if status == "continue":
                # Recursively get more feedback
                return self.get_feedback(packaging_manifest, validation_report)
        else:
            console.print(
                f"\n[dim]Minimum {self.min_rounds} round(s) required. "
                f"Round {self.current_round} of {self.min_rounds} complete.[/dim]"
            )
            status = "needs_revision"

        # Collect final comments
        comments = Prompt.ask("\nAdditional comments (optional)", default="")

        # Build refinements from answers
        refinements = self._build_refinements(answers)

        return json.dumps(
            {
                "status": status,
                "comments": comments,
                "refinements": refinements,
                "session_history": self.session_history,
                "rounds_completed": self.current_round,
                "reviewer": "human",
                "timestamp": datetime.now().isoformat(),
            }
        )

    def _generate_questions(
        self, manifest: dict, validation_report: dict, round_num: int
    ) -> list[dict]:
        """Generate clarifying questions based on the skill and current round."""
        questions = []

        if round_num == 1:
            # First round: Basic skill definition questions
            questions.append(
                {
                    "id": "scope_clarity",
                    "question": "Is the skill scope clearly defined?",
                    "context": "A well-defined scope helps differentiate this skill from similar ones.",
                    "options": [
                        {
                            "id": "a",
                            "label": "Yes, scope is clear",
                            "description": "The skill boundaries are well-defined",
                        },
                        {
                            "id": "b",
                            "label": "Needs more detail",
                            "description": "Add more specifics about what's included",
                        },
                        {
                            "id": "c",
                            "label": "Too broad",
                            "description": "Consider splitting into multiple skills",
                        },
                        {
                            "id": "d",
                            "label": "Too narrow",
                            "description": "Consider expanding the scope",
                        },
                    ],
                }
            )

            questions.append(
                {
                    "id": "capabilities_complete",
                    "question": "Are the listed capabilities complete?",
                    "context": "Capabilities should cover all major functions of the skill.",
                    "options": [
                        {
                            "id": "a",
                            "label": "Yes, complete",
                            "description": "All necessary capabilities are listed",
                        },
                        {
                            "id": "b",
                            "label": "Missing capabilities",
                            "description": "Some capabilities should be added",
                        },
                        {
                            "id": "c",
                            "label": "Too many capabilities",
                            "description": "Some should be removed or split",
                        },
                    ],
                }
            )

            questions.append(
                {
                    "id": "dependencies_correct",
                    "question": "Are the dependencies correctly identified?",
                    "context": "Dependencies should include all required skills without unnecessary ones.",
                    "options": [
                        {
                            "id": "a",
                            "label": "Yes, correct",
                            "description": "Dependencies are accurate",
                        },
                        {
                            "id": "b",
                            "label": "Missing dependencies",
                            "description": "Some required skills are not listed",
                        },
                        {
                            "id": "c",
                            "label": "Unnecessary dependencies",
                            "description": "Some listed dependencies aren't needed",
                        },
                    ],
                }
            )

        elif round_num == 2:
            # Second round: Quality and documentation questions
            questions.append(
                {
                    "id": "examples_quality",
                    "question": "How would you rate the usage examples?",
                    "context": "Good examples help users understand how to use the skill.",
                    "options": [
                        {
                            "id": "a",
                            "label": "Excellent",
                            "description": "Clear, practical, and comprehensive",
                        },
                        {"id": "b", "label": "Good", "description": "Useful but could be improved"},
                        {
                            "id": "c",
                            "label": "Needs improvement",
                            "description": "Examples are unclear or incomplete",
                        },
                        {"id": "d", "label": "Missing", "description": "No examples provided"},
                    ],
                }
            )

            questions.append(
                {
                    "id": "documentation_complete",
                    "question": "Is the documentation sufficient?",
                    "context": "Documentation should cover setup, usage, and troubleshooting.",
                    "options": [
                        {
                            "id": "a",
                            "label": "Yes, comprehensive",
                            "description": "All aspects are well-documented",
                        },
                        {
                            "id": "b",
                            "label": "Needs more detail",
                            "description": "Some areas need expansion",
                        },
                        {
                            "id": "c",
                            "label": "Major gaps",
                            "description": "Significant documentation missing",
                        },
                    ],
                }
            )

        elif round_num == 3:
            # Third round: Integration and compatibility questions
            questions.append(
                {
                    "id": "integration_ease",
                    "question": "How easy is it to integrate this skill?",
                    "context": "Consider the learning curve and setup requirements.",
                    "options": [
                        {
                            "id": "a",
                            "label": "Very easy",
                            "description": "Minimal setup, clear integration path",
                        },
                        {
                            "id": "b",
                            "label": "Moderate",
                            "description": "Some setup required, reasonable complexity",
                        },
                        {
                            "id": "c",
                            "label": "Complex",
                            "description": "Significant setup or learning required",
                        },
                    ],
                }
            )

            questions.append(
                {
                    "id": "naming_appropriate",
                    "question": "Is the skill naming appropriate?",
                    "context": "Names should be descriptive and follow conventions.",
                    "options": [
                        {
                            "id": "a",
                            "label": "Yes, appropriate",
                            "description": "Name clearly describes the skill",
                        },
                        {
                            "id": "b",
                            "label": "Could be clearer",
                            "description": "Name is acceptable but not ideal",
                        },
                        {
                            "id": "c",
                            "label": "Needs change",
                            "description": "Name is confusing or misleading",
                        },
                    ],
                }
            )

        else:
            # Fourth round: Final review questions
            questions.append(
                {
                    "id": "overall_quality",
                    "question": "What is your overall assessment of this skill?",
                    "context": "Consider all aspects: functionality, documentation, and usability.",
                    "options": [
                        {
                            "id": "a",
                            "label": "Ready for production",
                            "description": "Meets all quality standards",
                        },
                        {
                            "id": "b",
                            "label": "Minor improvements needed",
                            "description": "Small tweaks before approval",
                        },
                        {
                            "id": "c",
                            "label": "Major revision needed",
                            "description": "Significant changes required",
                        },
                        {
                            "id": "d",
                            "label": "Not suitable",
                            "description": "Does not meet requirements",
                        },
                    ],
                }
            )

            questions.append(
                {
                    "id": "additional_feedback",
                    "question": "Any additional feedback or suggestions?",
                    "context": "Free-form feedback for anything not covered above.",
                    "options": [],  # Free-form
                }
            )

        return questions

    def _build_refinements(self, answers: dict) -> list[str]:
        """Build list of refinements based on user answers."""
        refinements = []

        # Map answers to refinement suggestions
        refinement_map = {
            "scope_clarity": {
                "b": "Add more detail to skill scope definition",
                "c": "Consider splitting skill into smaller, focused skills",
                "d": "Expand skill scope to cover more use cases",
            },
            "capabilities_complete": {
                "b": "Add missing capabilities to the skill",
                "c": "Remove or consolidate redundant capabilities",
            },
            "dependencies_correct": {
                "b": "Add missing skill dependencies",
                "c": "Remove unnecessary dependencies",
            },
            "examples_quality": {
                "c": "Improve usage examples with clearer explanations",
                "d": "Add practical usage examples",
            },
            "documentation_complete": {
                "b": "Expand documentation with more details",
                "c": "Add missing documentation sections",
            },
            "integration_ease": {
                "c": "Simplify integration process or add setup guide",
            },
            "naming_appropriate": {
                "b": "Consider improving skill name for clarity",
                "c": "Rename skill to better reflect its purpose",
            },
            "overall_quality": {
                "b": "Apply minor improvements before final approval",
                "c": "Perform major revision based on feedback",
                "d": "Reconsider skill design and requirements",
            },
        }

        for question_id, answer in answers.items():
            if question_id in refinement_map:
                answer_key = answer if isinstance(answer, str) else answer[0] if answer else None
                if answer_key and answer_key in refinement_map[question_id]:
                    refinements.append(refinement_map[question_id][answer_key])

        return refinements


class WebhookFeedbackHandler(FeedbackHandler):
    """Send skill for review via webhook and wait for response."""

    def __init__(self, webhook_url: str, timeout: int = 3600):
        self.webhook_url = webhook_url
        self.timeout = timeout

    def get_feedback(self, packaging_manifest: str, validation_report: dict) -> str:
        """Post to webhook and wait for approval response."""

        import time

        import requests

        # Post review request
        review_data = {
            "manifest": packaging_manifest,
            "validation": validation_report,
            "timestamp": datetime.utcnow().isoformat(),
        }

        try:
            response = requests.post(self.webhook_url, json=review_data, timeout=10)
            review_id = response.json().get("review_id")

            # Poll for decision
            start_time = time.time()
            while time.time() - start_time < self.timeout:
                status_response = requests.get(f"{self.webhook_url}/{review_id}", timeout=5)

                if status_response.json().get("status") != "pending":
                    return json.dumps(status_response.json())

                time.sleep(30)  # Poll every 30 seconds

            # Timeout
            return json.dumps(
                {
                    "status": "needs_revision",
                    "comments": "Review timeout - please review manually",
                    "reviewer": "system",
                    "timestamp": datetime.utcnow().isoformat(),
                }
            )

        except Exception as e:
            logger.error(f"Webhook feedback error: {e}")
            return json.dumps(
                {
                    "status": "needs_revision",
                    "comments": f"Feedback system error: {str(e)}",
                    "reviewer": "system",
                    "timestamp": datetime.utcnow().isoformat(),
                }
            )


def create_feedback_handler(handler_type: str = "auto", **kwargs) -> FeedbackHandler:
    """Factory function for creating feedback handlers.

    Args:
        handler_type: Type of handler
            - "auto": Automatic approval based on validation (no HITL)
            - "cli": Simple CLI feedback (approve/revise/reject)
            - "interactive": Full HITL with multi-choice clarifying questions (recommended)
            - "webhook": External webhook-based review
        **kwargs: Additional arguments for specific handlers
            - For "interactive": min_rounds (default=1), max_rounds (default=4)
            - For "webhook": webhook_url (required), timeout (default=3600)

    Returns:
        FeedbackHandler instance

    Example:
        # For real HITL with clarifying questions (recommended for skill creation)
        handler = create_feedback_handler("interactive", min_rounds=1, max_rounds=4)

        # For automated testing/CI
        handler = create_feedback_handler("auto")
    """
    handlers = {
        "auto": AutoApprovalHandler,
        "cli": CLIFeedbackHandler,
        "interactive": InteractiveHITLHandler,
        "webhook": WebhookFeedbackHandler,
    }

    handler_class = handlers.get(handler_type)
    if not handler_class:
        raise ValueError(
            f"Unknown handler type: {handler_type}. Valid types: {', '.join(handlers.keys())}"
        )

    return handler_class(**kwargs)
