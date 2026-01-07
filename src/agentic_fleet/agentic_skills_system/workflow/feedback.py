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
        handler_type: Type of handler ("auto", "cli", "webhook")
        **kwargs: Additional arguments for specific handlers

    Returns:
        FeedbackHandler instance
    """
    handlers = {
        "auto": AutoApprovalHandler,
        "cli": CLIFeedbackHandler,
        "webhook": WebhookFeedbackHandler,
    }

    handler_class = handlers.get(handler_type)
    if not handler_class:
        raise ValueError(f"Unknown handler type: {handler_type}")

    return handler_class(**kwargs)
