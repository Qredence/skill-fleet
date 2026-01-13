"""Human feedback handlers for skill approval workflow."""

import json
import logging
from abc import ABC, abstractmethod
from datetime import datetime

logger = logging.getLogger(__name__)


# =============================================================================
# Refinement Mapping Constants
# =============================================================================

#: Maps question IDs and answer choices to refinement suggestions.
#: Used by InteractiveHITLHandler to convert user answers into actionable
#: refinement suggestions for skill improvement.
REFINEMENT_MAP: dict[str, dict[str, str]] = {
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


class FeedbackHandler(ABC):
    """Abstract base class for feedback handlers."""

    @abstractmethod
    def get_feedback(
        self,
        packaging_manifest: str,
        validation_report: dict,
        skill_content: str = "",
        task_description: str = "",
    ) -> str:
        """Get human feedback on packaged skill.

        Args:
            packaging_manifest: JSON string with skill metadata and manifest
            validation_report: Dict with validation results
            skill_content: The generated SKILL.md content (for review display)
            task_description: Original task description (for contextual questions)

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

    def get_feedback(
        self,
        packaging_manifest: str,
        validation_report: dict,
        skill_content: str = "",
        task_description: str = "",
    ) -> str:
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

    def get_feedback(
        self,
        packaging_manifest: str,
        validation_report: dict,
        skill_content: str = "",
        task_description: str = "",
    ) -> str:
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
    - Skill content display for informed review
    - Contextual questions based on task description
    - Dynamic LLM-generated questions (domain-aware, task-specific)
    """

    def __init__(self, min_rounds: int = 1, max_rounds: int = 4):
        self.min_rounds = max(1, min(min_rounds, 4))
        self.max_rounds = max(self.min_rounds, min(max_rounds, 4))
        self.current_round = 0
        self.session_history: list[dict] = []
        self.task_description = ""
        self.skill_content = ""

        # Initialize dynamic question generator
        from .modules import DynamicQuestionGeneratorModule

        self.question_generator = DynamicQuestionGeneratorModule()

    def get_feedback(
        self,
        packaging_manifest: str,
        validation_report: dict,
        skill_content: str = "",
        task_description: str = "",
    ) -> str:
        """Collect feedback via interactive multi-choice questions."""
        from rich.console import Console
        from rich.markdown import Markdown
        from rich.panel import Panel
        from rich.prompt import Prompt
        from rich.table import Table

        console = Console()
        self.current_round += 1
        self.task_description = task_description
        self.skill_content = skill_content

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
        if task_description:
            info_table.add_row(
                "Task",
                task_description[:80] + "..." if len(task_description) > 80 else task_description,
            )
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

        # Display generated skill content (the actual SKILL.md)
        if skill_content:
            console.print()
            # Truncate if very long, but show meaningful preview
            preview_lines = skill_content.split("\n")[:50]
            preview_content = "\n".join(preview_lines)
            if len(preview_lines) < len(skill_content.split("\n")):
                preview_content += f"\n\n... ({len(skill_content.split(chr(10))) - 50} more lines)"

            console.print(
                Panel(
                    Markdown(preview_content),
                    title="[bold green]Generated Skill Content (SKILL.md)[/bold green]",
                    border_style="green",
                    expand=False,
                )
            )

        # Show capabilities if available
        capabilities = manifest.get("capabilities", [])
        if capabilities:
            console.print("\n[bold cyan]Capabilities:[/bold cyan]")
            for cap in capabilities[:5]:
                if isinstance(cap, dict):
                    cap_name = cap.get("name", cap.get("id", "Unknown"))
                    cap_desc = cap.get("description", "")[:60]
                    console.print(f"  • [cyan]{cap_name}[/cyan]: {cap_desc}")
                else:
                    console.print(f"  • {cap}")
            if len(capabilities) > 5:
                console.print(f"  ... and {len(capabilities) - 5} more")

        # Generate clarifying questions based on current round
        # Use dynamic LLM-based question generation instead of static templates
        questions = self._generate_questions_dynamic(
            manifest, validation_report, self.current_round
        )

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
        """Generate contextual clarifying questions based on the skill and current round.

        Questions are tailored to the specific skill being reviewed, using:
        - skill_name, skill_id from manifest
        - task_description from the original request
        - capabilities from the generated skill
        """
        questions = []

        # Extract skill context for contextual questions
        skill_name = manifest.get("name", "this skill")
        capabilities = manifest.get("capabilities", [])
        cap_names = []
        for cap in capabilities[:3]:
            if isinstance(cap, dict):
                cap_names.append(cap.get("name", cap.get("id", "")))
            else:
                cap_names.append(str(cap))
        cap_list = ", ".join(cap_names) if cap_names else "the listed capabilities"

        task_context = self.task_description if self.task_description else "the requested task"

        if round_num == 1:
            # First round: Skill scope and alignment questions (contextual)
            questions.append(
                {
                    "id": "scope_clarity",
                    "question": f"Does '{skill_name}' clearly address '{task_context[:50]}...'?",
                    "context": f"The skill should provide the capabilities needed for: {task_context}",
                    "options": [
                        {
                            "id": "a",
                            "label": "Yes, fully addresses the task",
                            "description": f"'{skill_name}' covers all aspects of the requested task",
                        },
                        {
                            "id": "b",
                            "label": "Partially addresses it",
                            "description": "Some aspects of the task are missing",
                        },
                        {
                            "id": "c",
                            "label": "Too broad for the task",
                            "description": "Skill covers more than needed, consider splitting",
                        },
                        {
                            "id": "d",
                            "label": "Too narrow for the task",
                            "description": "Skill doesn't fully cover the requested capability",
                        },
                    ],
                }
            )

            questions.append(
                {
                    "id": "capabilities_complete",
                    "question": f"Are these capabilities sufficient: {cap_list}?",
                    "context": f"These capabilities should enable: {task_context[:80]}",
                    "options": [
                        {
                            "id": "a",
                            "label": "Yes, capabilities are complete",
                            "description": "All necessary capabilities for the task are listed",
                        },
                        {
                            "id": "b",
                            "label": "Missing key capabilities",
                            "description": "Important capabilities for the task are not included",
                        },
                        {
                            "id": "c",
                            "label": "Has unnecessary capabilities",
                            "description": "Some capabilities are not relevant to the task",
                        },
                    ],
                }
            )

            questions.append(
                {
                    "id": "dependencies_correct",
                    "question": f"Are the dependencies for '{skill_name}' correctly identified?",
                    "context": "Dependencies should include all required foundational skills.",
                    "options": [
                        {
                            "id": "a",
                            "label": "Yes, dependencies are correct",
                            "description": "All required skills are listed as dependencies",
                        },
                        {
                            "id": "b",
                            "label": "Missing dependencies",
                            "description": "Some foundational skills are not listed",
                        },
                        {
                            "id": "c",
                            "label": "Unnecessary dependencies",
                            "description": "Some listed dependencies aren't actually needed",
                        },
                    ],
                }
            )

        elif round_num == 2:
            # Second round: Content quality questions
            questions.append(
                {
                    "id": "examples_quality",
                    "question": f"Do the examples show how to use '{skill_name}' effectively?",
                    "context": f"Examples should demonstrate practical usage for: {task_context[:60]}",
                    "options": [
                        {
                            "id": "a",
                            "label": "Excellent examples",
                            "description": "Clear, practical examples that demonstrate the skill",
                        },
                        {
                            "id": "b",
                            "label": "Good but could improve",
                            "description": "Useful but need more detail or variety",
                        },
                        {
                            "id": "c",
                            "label": "Need better examples",
                            "description": "Examples are unclear or don't match the task",
                        },
                        {
                            "id": "d",
                            "label": "Examples missing",
                            "description": "No practical examples provided",
                        },
                    ],
                }
            )

            questions.append(
                {
                    "id": "documentation_complete",
                    "question": f"Is the documentation for '{skill_name}' sufficient?",
                    "context": "Documentation should explain how to use this skill effectively.",
                    "options": [
                        {
                            "id": "a",
                            "label": "Comprehensive documentation",
                            "description": "All aspects are well-documented",
                        },
                        {
                            "id": "b",
                            "label": "Needs more detail",
                            "description": "Some areas need better explanation",
                        },
                        {
                            "id": "c",
                            "label": "Major gaps in documentation",
                            "description": "Important information is missing",
                        },
                    ],
                }
            )

        elif round_num == 3:
            # Third round: Integration and naming
            questions.append(
                {
                    "id": "integration_ease",
                    "question": f"How easy would it be to integrate '{skill_name}' into a workflow?",
                    "context": "Consider the learning curve and setup requirements.",
                    "options": [
                        {
                            "id": "a",
                            "label": "Very easy to integrate",
                            "description": "Minimal setup, clear integration path",
                        },
                        {
                            "id": "b",
                            "label": "Moderate complexity",
                            "description": "Some setup required, reasonable complexity",
                        },
                        {
                            "id": "c",
                            "label": "Complex integration",
                            "description": "Significant setup or learning required",
                        },
                    ],
                }
            )

            questions.append(
                {
                    "id": "naming_appropriate",
                    "question": f"Is '{skill_name}' a good name for this skill?",
                    "context": f"The name should clearly indicate it handles: {task_context[:50]}",
                    "options": [
                        {
                            "id": "a",
                            "label": "Name is appropriate",
                            "description": "Name clearly describes what the skill does",
                        },
                        {
                            "id": "b",
                            "label": "Could be clearer",
                            "description": "Name is acceptable but not ideal",
                        },
                        {
                            "id": "c",
                            "label": "Needs different name",
                            "description": "Name is confusing or misleading",
                        },
                    ],
                }
            )

        else:
            # Fourth round: Final review
            questions.append(
                {
                    "id": "overall_quality",
                    "question": f"Overall, does '{skill_name}' meet the requirements for '{task_context[:40]}...'?",
                    "context": "Consider all aspects: functionality, documentation, and usability.",
                    "options": [
                        {
                            "id": "a",
                            "label": "Ready for production",
                            "description": "Skill meets all quality standards",
                        },
                        {
                            "id": "b",
                            "label": "Minor improvements needed",
                            "description": "Small tweaks before final approval",
                        },
                        {
                            "id": "c",
                            "label": "Major revision needed",
                            "description": "Significant changes required",
                        },
                        {
                            "id": "d",
                            "label": "Does not meet requirements",
                            "description": "Skill fundamentally misses the mark",
                        },
                    ],
                }
            )

            questions.append(
                {
                    "id": "additional_feedback",
                    "question": f"Any specific feedback for improving '{skill_name}'?",
                    "context": "Free-form feedback for anything not covered above.",
                    "options": [],  # Free-form
                }
            )

        return questions

    def _generate_questions_dynamic(
        self, manifest: dict, validation_report: dict, round_num: int
    ) -> list[dict]:
        """Generate dynamic, domain-aware questions using LLM.

        Uses DynamicQuestionGeneratorModule to create contextual questions
        that are specific to the task, domain, and skill being reviewed.

        Falls back to static template questions if LLM generation fails.
        """
        # Build previous feedback context
        previous_feedback = ""
        if self.session_history:
            for item in self.session_history[-1:]:
                feedback_items = item.get("refinements", [])
                if feedback_items:
                    previous_feedback = "Previous feedback: " + "; ".join(feedback_items)

        try:
            # Call the dynamic question generator
            result = self.question_generator(
                task_description=self.task_description,
                skill_metadata=manifest,
                skill_content=self.skill_content[:500] if self.skill_content else "",
                validation_report=validation_report,
                round_number=round_num,
                previous_feedback=previous_feedback,
            )

            questions = result.get("questions", [])

            # Validate that we got proper questions
            if questions and isinstance(questions, list) and len(questions) > 0:
                # Ensure each question has required fields
                valid_questions = []
                for q in questions:
                    if isinstance(q, dict) and q.get("question") and q.get("options"):
                        # Ensure required fields exist
                        q.setdefault("id", q.get("id", f"question_{len(valid_questions)}"))
                        q.setdefault("context", "")
                        valid_questions.append(q)

                if valid_questions:
                    return valid_questions

        except Exception as e:
            logger.warning(f"Dynamic question generation failed: {e}, using fallback")

        # Fallback to static template questions
        return self._generate_questions(manifest, validation_report, round_num)

    def _build_refinements(self, answers: dict) -> list[str]:
        """Build list of refinements based on user answers.

        Uses the module-level REFINEMENT_MAP to convert user answer
        choices into actionable refinement suggestions.
        """
        refinements = []

        for question_id, answer in answers.items():
            if question_id in REFINEMENT_MAP:
                # Handle both single (str) and multiple (list) answers
                answer_keys = answer if isinstance(answer, list) else [answer]
                for answer_key in answer_keys:
                    if answer_key and answer_key in REFINEMENT_MAP[question_id]:
                        refinements.append(REFINEMENT_MAP[question_id][answer_key])

        return refinements


class WebhookFeedbackHandler(FeedbackHandler):
    """Send skill for review via webhook and wait for response."""

    def __init__(self, webhook_url: str, timeout: int = 3600):
        self.webhook_url = webhook_url
        self.timeout = timeout

    def get_feedback(
        self,
        packaging_manifest: str,
        validation_report: dict,
        skill_content: str = "",
        task_description: str = "",
    ) -> str:
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
