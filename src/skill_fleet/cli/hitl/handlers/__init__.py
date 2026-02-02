"""
CLI interaction handlers for HITL workflow.

Each handler is responsible for:
1. Rendering the interaction prompt to the user
2. Collecting user response via the UI
3. Posting the response back to the API

This keeps the runner focused on polling/coordination while
each handler encapsulates the interaction logic for its type.
"""

from __future__ import annotations

from typing import Any, cast

from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel

from ...ui.prompts import PromptUI, get_default_ui


class InteractionHandler:
    """
    Base class for HITL interaction handlers.

    All handlers must implement the handle() method which takes
    the prompt data from the API and posts a response back.
    """

    def __init__(self, console: Console, ui: PromptUI | None = None) -> None:
        """
        Initialize the handler.

        Args:
            console: Rich console for rendering output
            ui: PromptUI for user input (uses default if None)
        """
        self.console = console
        self.ui = ui or get_default_ui()

    async def handle(
        self,
        job_id: str,
        prompt_data: dict[str, Any],
        client: Any,
    ) -> None:
        """
        Handle the interaction and post response to API.

        Args:
            job_id: The job ID for this interaction
            prompt_data: The prompt data from GET /hitl/{job_id}/prompt
            client: The API client for posting responses

        Raises:
            NotImplementedError: Subclasses must implement this
        """
        raise NotImplementedError


class DeepUnderstandingHandler(InteractionHandler):
    """
    Handler for deep_understanding interaction type.

    Asks WHY questions to understand the user's true problem and goals.
    Shows research performed and current understanding.

    User Actions:
    - proceed: Answer question and provide context
    - skip: Skip this question
    - cancel: Cancel skill creation
    """

    async def handle(
        self,
        job_id: str,
        prompt_data: dict[str, Any],
        client: Any,
    ) -> None:
        """Handle deep understanding interaction and post response to API."""
        question = prompt_data.get("question", "")
        research = prompt_data.get("research_performed", [])
        current = prompt_data.get("current_understanding", "")
        readiness_score = prompt_data.get("readiness_score")

        # Show current understanding
        if current:
            self.console.print(
                Panel(
                    Markdown(current) if current else "No understanding yet.",
                    title="[bold cyan]💭 Current Understanding[/bold cyan]",
                    border_style="cyan",
                )
            )

        # Show research performed
        if research:
            self.console.print("[dim]Research performed:[/dim]")
            for r in research:
                self.console.print(f"  • {r}")

        if readiness_score is not None:
            self.console.print(f"[dim]Readiness score:[/dim] {readiness_score:.2f} (target 0.80)")

        # Ask the question
        if question:
            self.console.print(
                Panel(
                    Markdown(question) if "**" in question else question,
                    title="[bold yellow]🤔 Deep Understanding Question[/bold yellow]",
                    border_style="yellow",
                )
            )

        action = await self.ui.choose_one(
            "Continue?",
            [
                ("proceed", "Answer & Continue"),
                ("skip", "Skip Question"),
                ("cancel", "Cancel"),
            ],
            default_id="proceed",
        )

        if action == "cancel":
            await client.post_hitl_response(job_id, {"action": "cancel"})
        elif action == "proceed":
            answer = await self.ui.ask_text("Your answer (or /cancel)", default="")
            if answer.strip().lower() in {"/cancel", "/exit", "/quit"}:
                await client.post_hitl_response(job_id, {"action": "cancel"})
            else:
                # Ask for additional context
                problem = await self.ui.ask_text(
                    "What problem are you solving? (optional)", default=""
                )
                goals_input = await self.ui.ask_text(
                    "What are your goals? (comma-separated, optional)", default=""
                )
                goals = (
                    [g.strip() for g in goals_input.split(",") if g.strip()] if goals_input else []
                )

                await client.post_hitl_response(
                    job_id,
                    {
                        "action": "proceed",
                        "answer": answer,
                        "problem": problem,
                        "goals": goals,
                    },
                )
        else:  # skip
            await client.post_hitl_response(job_id, {"action": "proceed"})


class TDDRedHandler(InteractionHandler):
    """
    Handler for tdd_red interaction type.

    TDD Red Phase: User writes failing tests before implementation.
    Shows test requirements, acceptance criteria, and checklist.
    Tracks any rationalizations detected.

    User Actions:
    - proceed: Tests written and failing as expected
    - revise: Revise the test requirements
    - cancel: Cancel skill creation
    """

    async def handle(
        self,
        job_id: str,
        prompt_data: dict[str, Any],
        client: Any,
    ) -> None:
        """Handle TDD red phase interaction and post response to API."""
        requirements = prompt_data.get("test_requirements", "")
        acceptance = prompt_data.get("acceptance_criteria", [])
        checklist = prompt_data.get("checklist_items", [])
        rationalizations = prompt_data.get("rationalizations_identified", [])

        self.console.print(
            Panel(
                Markdown(requirements) if "**" in requirements else requirements,
                title="[bold red]🔴 TDD Red Phase: Write Failing Tests[/bold red]",
                border_style="red",
            )
        )

        if acceptance:
            self.console.print("[dim]Acceptance criteria:[/dim]")
            for i, criterion in enumerate(acceptance, 1):
                self.console.print(f"  {i}. {criterion}")

        if checklist:
            self.console.print("[dim]Checklist:[/dim]")
            for _i, item in enumerate(checklist, 1):
                text = item.get("text", item) if isinstance(item, dict) else item
                done = item.get("done", False) if isinstance(item, dict) else False
                self.console.print(f"  {'☑' if done else '☐'} {text}")

        if rationalizations:
            self.console.print("[yellow]Rationalizations detected:[/yellow]")
            for r in rationalizations:
                self.console.print(f"  ⚠️  {r}")

        action = await self.ui.choose_one(
            "Tests written?",
            [
                ("proceed", "Yes, tests fail as expected"),
                ("revise", "Revise requirements"),
                ("cancel", "Cancel"),
            ],
            default_id="proceed",
        )

        payload: dict[str, object] = {"action": action}
        if action == "revise":
            payload["feedback"] = await self.ui.ask_text("What should change?", default="")
        await client.post_hitl_response(job_id, payload)


class TDDGreenHandler(InteractionHandler):
    """
    Handler for tdd_green interaction type.

    TDD Green Phase: User makes tests pass with minimal implementation.
    Shows failing test name, location, and implementation hint.

    User Actions:
    - proceed: All tests passing
    - revise: Need adjustment to approach
    - cancel: Cancel skill creation
    """

    async def handle(
        self,
        job_id: str,
        prompt_data: dict[str, Any],
        client: Any,
    ) -> None:
        """Handle TDD green phase interaction and post response to API."""
        failing_test = prompt_data.get("failing_test", "")
        test_location = prompt_data.get("test_location", "")
        hint = prompt_data.get("minimal_implementation_hint", "")

        content = f"[bold]Failing Test:[/bold] {failing_test}"
        if test_location:
            content += f"\n\n[dim]Location:[/dim] {test_location}"
        if hint:
            content += f"\n\n[dim]Hint:[/dim] {hint}"

        self.console.print(
            Panel(
                content,
                title="[bold green]🟢 TDD Green Phase: Make Tests Pass[/bold green]",
                border_style="green",
            )
        )

        action = await self.ui.choose_one(
            "Tests passing?",
            [
                ("proceed", "Yes, all tests pass"),
                ("revise", "Need adjustment"),
                ("cancel", "Cancel"),
            ],
            default_id="proceed",
        )

        payload: dict[str, object] = {"action": action}
        if action == "revise":
            payload["feedback"] = await self.ui.ask_text("What needs adjustment?", default="")
        await client.post_hitl_response(job_id, payload)


class TDDRefactorHandler(InteractionHandler):
    """
    Handler for tdd_refactor interaction type.

    TDD Refactor Phase: User cleans up code while keeping tests passing.
    Shows refactor opportunities, code smells, and coverage report.

    User Actions:
    - proceed: Code refactored successfully
    - skip: Skip refactoring step
    - revise: Still working on refactoring
    - cancel: Cancel skill creation
    """

    async def handle(
        self,
        job_id: str,
        prompt_data: dict[str, Any],
        client: Any,
    ) -> None:
        """Handle TDD refactor phase interaction and post response to API."""
        opportunities = prompt_data.get("refactor_opportunities", [])
        code_smells = prompt_data.get("code_smells", [])
        coverage = prompt_data.get("coverage_report", "")

        content_parts = []
        if coverage:
            content_parts.append(f"[bold]Coverage:[/bold] {coverage}")
        if opportunities:
            content_parts.append("[bold]Refactor opportunities:[/bold]")
            content_parts.extend(f"  • {op}" for op in opportunities)
        if code_smells:
            if opportunities:
                content_parts.append("")  # blank line
            content_parts.append("[yellow]Code smells:[/yellow]")
            content_parts.extend(f"  ⚠️  {smell}" for smell in code_smells)

        self.console.print(
            Panel(
                "\n".join(str(p) for p in content_parts) if content_parts else "Ready to refactor.",
                title="[bold blue]🔵 TDD Refactor Phase: Clean Up Code[/bold blue]",
                border_style="blue",
            )
        )

        action = await self.ui.choose_one(
            "Refactoring complete?",
            [
                ("proceed", "Yes, code refactored"),
                ("skip", "Skip refactoring"),
                ("revise", "Need more work"),
                ("cancel", "Cancel"),
            ],
            default_id="proceed",
        )

        # Map skip to proceed (user chose to skip refactoring step)
        if action == "skip":
            action = "proceed"

        payload: dict[str, object] = {"action": action}
        if action == "revise":
            payload["feedback"] = await self.ui.ask_text("What still needs work?", default="")
        await client.post_hitl_response(job_id, payload)


class ClarifyHandler(InteractionHandler):
    """
    Handler for clarify interaction type.

    Asks clarification questions to understand user requirements better.
    Supports single/multiple choice questions with "Other" option.

    User Actions:
    - answer: Provide answers to questions
    - cancel: Cancel skill creation
    """

    async def handle(
        self,
        job_id: str,
        prompt_data: dict[str, Any],
        client: Any,
    ) -> None:
        """Handle clarification interaction and post response to API."""
        rationale = prompt_data.get("rationale", "")
        if rationale:
            self.console.print(
                Panel(
                    Markdown(rationale) if "**" in rationale else rationale,
                    title="[dim]Why I'm asking[/dim]",
                    border_style="dim",
                )
            )

        questions_list = self._normalize_questions(prompt_data.get("questions"))
        if not questions_list:
            self.console.print(
                Panel(
                    "Please provide additional information.",
                    title="[bold yellow]🤔 Clarification Needed[/bold yellow]",
                    border_style="yellow",
                )
            )
            answer = await self.ui.ask_text("Your response (or /cancel)", default="")
            if answer.strip().lower() in {"/cancel", "/exit", "/quit"}:
                await client.post_hitl_response(job_id, {"action": "cancel"})
            else:
                await client.post_hitl_response(job_id, {"answers": {"response": answer}})
            return

        self.console.print(
            Panel(
                "Answer the following question(s) one at a time.",
                title="[bold yellow]🤔 Clarification Needed[/bold yellow]",
                border_style="yellow",
            )
        )

        answer_blocks: list[str] = []
        for idx, question in enumerate(questions_list, 1):
            q_text = self._question_text(question)
            choices, allows_multiple = self._question_options(question)

            self.console.print(
                Panel(
                    Markdown(q_text) if any(tok in q_text for tok in ("**", "`", "\n")) else q_text,
                    title=f"[bold yellow]Question {idx}/{len(questions_list)}[/bold yellow]",
                    border_style="yellow",
                )
            )

            if choices:
                from ...ui.prompts import choose_many_with_other, choose_one_with_other

                if allows_multiple:
                    selected_ids, free_text = await choose_many_with_other(
                        self.ui,
                        "Select option(s)",
                        choices,
                    )
                else:
                    selected_ids, free_text = await choose_one_with_other(
                        self.ui,
                        "Select one option",
                        choices,
                    )
                selected_labels = [label for opt_id, label in choices if opt_id in selected_ids]
                answer = ", ".join(selected_labels)
                if free_text.strip():
                    answer = f"{answer}\nOther: {free_text}" if answer else free_text
            else:
                answer = await self.ui.ask_text("Your answer (or /cancel)", default="")
                if answer.strip().lower() in {"/cancel", "/exit", "/quit"}:
                    await client.post_hitl_response(job_id, {"action": "cancel"})
                    return

            answer_blocks.append(f"Q{idx}: {q_text}\nA{idx}: {answer}")

        combined = "\n\n".join(answer_blocks).strip()
        await client.post_hitl_response(job_id, {"answers": {"response": combined}})

    @staticmethod
    def _normalize_questions(questions: object) -> list[object]:
        """Normalize questions from API response."""
        if questions is None:
            return []
        if isinstance(questions, list):
            return list(questions)
        return [questions]

    @staticmethod
    def _question_text(question: object) -> str:
        """Extract question text from a StructuredQuestion dict."""
        if isinstance(question, str):
            return question
        if isinstance(question, dict):
            q_dict = cast(dict[str, Any], question)
            return str(q_dict.get("text") or q_dict.get("question") or question)
        return str(question)

    @staticmethod
    def _question_options(question: object) -> tuple[list[tuple[str, str]], bool]:
        """Extract options from a StructuredQuestion dict."""
        if not isinstance(question, dict):
            return ([], False)

        q_dict = cast(dict[str, Any], question)
        raw_options = q_dict.get("options")
        if not isinstance(raw_options, list) or not raw_options:
            return ([], False)

        choices: list[tuple[str, str]] = []
        for opt in raw_options:
            if isinstance(opt, dict):
                opt_dict = cast(dict[str, Any], opt)
                opt_id = str(opt_dict.get("id") or opt_dict.get("value") or "")
                label = str(opt_dict.get("label") or opt_dict.get("text") or opt_id)
                desc = opt_dict.get("description")
                if desc:
                    label = f"{label} — {desc}"
                if opt_id:
                    choices.append((opt_id, label))
            else:
                choices.append((str(opt), str(opt)))

        allows_multiple = bool(q_dict.get("allows_multiple", False))
        return (choices, allows_multiple)


class ConfirmHandler(InteractionHandler):
    """
    Handler for confirm interaction type.

    Shows understanding summary and asks user to confirm before proceeding.
    Displays proposed taxonomy path and key assumptions.

    User Actions:
    - proceed: Confirm understanding and continue
    - revise: Request changes
    - cancel: Cancel skill creation
    """

    async def handle(
        self,
        job_id: str,
        prompt_data: dict[str, Any],
        client: Any,
    ) -> None:
        """Handle confirmation interaction and post response to API."""
        rationale = prompt_data.get("rationale", "")
        if rationale:
            self.console.print(
                Panel(
                    Markdown(rationale) if "**" in rationale else rationale,
                    title="[dim]💭 Reasoning[/dim]",
                    border_style="dim",
                )
            )

        summary = prompt_data.get("summary", "")
        path = prompt_data.get("path", "")
        key_assumptions = prompt_data.get("key_assumptions", [])

        self.console.print(
            Panel(
                Markdown(summary) if summary else "No summary available.",
                title="[bold cyan]📋 Understanding Summary[/bold cyan]",
                border_style="cyan",
            )
        )
        if path:
            self.console.print(f"[dim]Proposed path: {path}[/dim]")
        if key_assumptions:
            self.console.print("[dim]Key assumptions:[/dim]")
            for assumption in key_assumptions:
                self.console.print(f"  • {assumption}")

        action = await self.ui.choose_one(
            "Proceed?",
            [("proceed", "Proceed"), ("revise", "Revise"), ("cancel", "Cancel")],
            default_id="proceed",
        )

        payload: dict[str, object] = {"action": action}
        if action == "revise":
            payload["feedback"] = await self.ui.ask_text("What should change?", default="")
        await client.post_hitl_response(job_id, payload)


class PreviewHandler(InteractionHandler):
    """
    Handler for preview interaction type.

    Shows generated content preview with highlights before validation.
    Allows user to request refinement if needed.

    User Actions:
    - proceed: Accept preview and continue
    - refine: Request content improvements
    - cancel: Cancel skill creation
    """

    async def handle(
        self,
        job_id: str,
        prompt_data: dict[str, Any],
        client: Any,
    ) -> None:
        """Handle preview interaction and post response to API."""
        rationale = prompt_data.get("rationale", "")
        if rationale:
            self.console.print(
                Panel(
                    Markdown(rationale) if "**" in rationale else rationale,
                    title="[dim]💭 Generation Reasoning[/dim]",
                    border_style="dim",
                )
            )

        content = prompt_data.get("content", "")
        highlights = prompt_data.get("highlights", [])

        self.console.print(
            Panel(
                Markdown(content) if content else "No preview available.",
                title="[bold blue]📝 Content Preview[/bold blue]",
                border_style="blue",
            )
        )
        if highlights:
            self.console.print("[dim]Highlights:[/dim]")
            for h in highlights:
                self.console.print(f"  • {h}")

        action = await self.ui.choose_one(
            "Looks good?",
            [("proceed", "Proceed"), ("refine", "Refine"), ("cancel", "Cancel")],
            default_id="proceed",
        )

        payload: dict[str, object] = {"action": action}
        if action == "refine":
            payload["feedback"] = await self.ui.ask_text("What should be improved?", default="")
        await client.post_hitl_response(job_id, payload)


class ValidateHandler(InteractionHandler):
    """
    Handler for validate interaction type.

    Shows validation report with any issues found.
    Allows user to accept or request fixes.

    User Actions:
    - proceed: Accept validation results
    - refine: Request fixes for issues
    - cancel: Cancel skill creation
    """

    async def handle(
        self,
        job_id: str,
        prompt_data: dict[str, Any],
        client: Any,
    ) -> None:
        """Handle validation interaction and post response to API."""
        report = prompt_data.get("report", "")
        passed = prompt_data.get("passed", False)
        title_style = "green" if passed else "red"
        title_icon = "✅" if passed else "⚠️"

        self.console.print(
            Panel(
                Markdown(report) if report else "No report available.",
                title=f"[bold {title_style}]{title_icon} Validation Report[/bold {title_style}]",
                border_style=title_style,
            )
        )

        action = await self.ui.choose_one(
            "Accept?",
            [("proceed", "Proceed"), ("refine", "Refine"), ("cancel", "Cancel")],
            default_id="proceed",
        )

        payload: dict[str, object] = {"action": action}
        if action == "refine":
            payload["feedback"] = await self.ui.ask_text("What should be improved?", default="")
        await client.post_hitl_response(job_id, payload)


# Handler registry - maps interaction types to handler classes
HANDLERS: dict[str, type[InteractionHandler]] = {
    "deep_understanding": DeepUnderstandingHandler,
    "tdd_red": TDDRedHandler,
    "tdd_green": TDDGreenHandler,
    "tdd_refactor": TDDRefactorHandler,
    "clarify": ClarifyHandler,
    "confirm": ConfirmHandler,
    "preview": PreviewHandler,
    "validate": ValidateHandler,
}


def get_handler(
    interaction_type: str, console: Console, ui: PromptUI | None = None
) -> InteractionHandler | None:
    """
    Get a handler instance for the given interaction type.

    Args:
        interaction_type: The HITL interaction type (e.g., "deep_understanding")
        console: Rich console for rendering
        ui: PromptUI for user input (uses default if None)

    Returns:
        Handler instance or None if interaction_type not registered
    """
    handler_class = HANDLERS.get(interaction_type)
    if handler_class:
        return handler_class(console, ui)
    return None


__all__ = [
    "InteractionHandler",
    "DeepUnderstandingHandler",
    "TDDRedHandler",
    "TDDGreenHandler",
    "TDDRefactorHandler",
    "ClarifyHandler",
    "ConfirmHandler",
    "PreviewHandler",
    "ValidateHandler",
    "get_handler",
]
