"""Interactive CLI for conversational skill creation.

Provides a Rich-based chat interface where users converse naturally
with an AI agent that uses DSPy framework internally to create skills.
"""

from __future__ import annotations

import json
import logging
import sys
from pathlib import Path
from typing import Any

from rich.console import Console
from rich.live import Live
from rich.markdown import Markdown
from rich.panel import Panel
from rich.prompt import Prompt
from rich.table import Table
from rich.text import Text

from ..agent.agent import (
    AgentResponse,
    ConversationalSkillAgent,
    ConversationSession,
    ConversationState,
)
from ..taxonomy.manager import TaxonomyManager

logger = logging.getLogger(__name__)


class InteractiveSkillCLI:
    """Interactive CLI for skill creation through natural conversation."""

    def __init__(
        self,
        taxonomy_manager: TaxonomyManager,
        config: dict[str, Any],
        skills_root: Path,
        user_id: str = "default",
    ):
        """Initialize interactive CLI.

        Args:
            taxonomy_manager: Taxonomy management instance
            config: Fleet config dictionary
            skills_root: Skills root directory
            user_id: User ID for context
        """
        self.taxonomy = taxonomy_manager
        self.config = config
        self.skills_root = skills_root
        self.user_id = user_id
        self.console = Console()

        # Build task LMs from config
        from ..llm import build_lm_for_task

        task_names = [
            "skill_understand",
            "skill_plan",
            "skill_initialize",
            "skill_edit",
            "skill_package",
            "skill_validate",
        ]
        task_lms = {task_name: build_lm_for_task(config, task_name) for task_name in task_names}

        # Add conversational_agent task type (if not in config, use skill_understand as default)
        if "conversational_agent" not in task_names:
            # Try to build from config, fallback to skill_understand
            try:
                task_lms["conversational_agent"] = build_lm_for_task(config, "skill_understand")
            except Exception:
                # Use skill_understand LM as fallback
                task_lms["conversational_agent"] = task_lms["skill_understand"]

        # Initialize conversational agent
        self.agent = ConversationalSkillAgent(
            taxonomy_manager=taxonomy_manager,
            task_lms=task_lms,
            skills_root=skills_root,
        )

        # Initialize session
        self.session = ConversationSession()
        self.session_file = skills_root / ".interactive_session.json"

        # Load session if exists
        if self.session_file.exists():
            try:
                data = json.loads(self.session_file.read_text(encoding="utf-8"))
                self.session = ConversationSession.from_dict(data)
                self.console.print("[dim]Loaded previous session[/dim]\n")
            except Exception as e:
                self.console.print(f"[yellow]Could not load session: {e}[/yellow]\n")

    def run(self) -> int:
        """Run the interactive CLI main loop.

        Returns:
            Exit code (0 for success, 1 for error)
        """
        self.console.print(
            Panel.fit(
                "[bold cyan]Skills Fleet - Interactive Mode[/bold cyan]\n"
                "Chat with an AI agent to create well-crafted skills.\n"
                "Type /help for commands, /exit to quit.",
                border_style="cyan",
            )
        )
        self.console.print()

        # Initial greeting
        welcome_response = self.agent.respond("", self.session, capture_thinking=False)
        if welcome_response.message:
            self.console.print(f"[cyan]Agent:[/cyan] {welcome_response.message}\n")

        # Main chat loop
        while True:
            try:
                # Display checklist status if in TDD phases
                if self.session.state in [
                    ConversationState.TDD_RED_PHASE,
                    ConversationState.TDD_GREEN_PHASE,
                    ConversationState.TDD_REFACTOR_PHASE,
                    ConversationState.CHECKLIST_COMPLETE,
                ]:
                    self._display_checklist_status()

                # Display multi-skill queue if active
                if self.session.multi_skill_queue:
                    self._display_multi_skill_queue()

                # Prompt user
                user_input = Prompt.ask("[bold green]You:[/bold green]")

                if not user_input.strip():
                    continue

                # Handle commands
                if user_input.startswith("/"):
                    result = self._handle_command(user_input)
                    if result == "exit":
                        return 0
                    elif result == "continue":
                        continue
                    # Otherwise fall through to process as regular message

                # Get agent response with real-time streaming display
                response = self._respond_with_streaming(user_input)

                # Note: Thinking content is already displayed via streaming
                # No need to display it again here

                # Handle special action: ask_understanding_question (for deep understanding phase)
                if response.action == "ask_understanding_question":
                    question_data = response.data.get("question")
                    reasoning = response.data.get("reasoning", response.thinking_content)
                    if question_data:
                        # Parse ClarifyingQuestion from dict
                        from ..core.models import ClarifyingQuestion

                        if isinstance(question_data, dict):
                            question = ClarifyingQuestion(**question_data)
                        else:
                            question = question_data

                        user_answer = self._display_multi_choice_question(question, reasoning)
                        # Store question in session for answer tracking
                        if self.session.deep_understanding:
                            self.session.deep_understanding["current_question"] = question_data
                        # Process answer immediately
                        next_response = self._respond_with_streaming(user_answer)
                        # Note: Thinking already displayed via streaming, just show message
                        if next_response.message:
                            self.console.print(f"[cyan]Agent:[/cyan] {next_response.message}")
                        continue

                # Display agent response
                if response.message:
                    # Check if this is a yes/no question that needs better formatting
                    if (
                        response.state == ConversationState.TDD_REFACTOR_PHASE
                        and "yes/no" in response.message.lower()
                    ):
                        # Format yes/no questions with better visibility
                        self.console.print("\n[bold yellow]⚠ Decision required:[/bold yellow]\n")
                        self.console.print(
                            Panel(
                                response.message,
                                border_style="yellow",
                                title="[yellow]Question[/yellow]",
                            )
                        )
                        self.console.print()
                    # Format markdown if present
                    elif "**" in response.message or "```" in response.message:
                        self.console.print("[cyan]Agent:[/cyan]")
                        self.console.print(Markdown(response.message))
                    else:
                        self.console.print(f"[cyan]Agent:[/cyan] {response.message}")

                self.console.print()

                # Handle non-blocking actions (agent continues without user input)
                if not response.requires_user_input:
                    # Agent is executing something (creating skill, running tests, etc.)
                    if response.action in (
                        "skill_created",
                        "tdd_red_complete",
                        "tdd_green_complete",
                        "revising",
                        "deep_understanding_complete",
                    ):
                        # Agent has completed an action, automatically continue to next phase
                        if response.action == "tdd_red_complete":
                            # Automatically continue to GREEN phase
                            response = self._respond_with_streaming("continue")
                            # Display just the message (thinking already shown via streaming)
                            if response.message:
                                self.console.print(f"[cyan]Agent:[/cyan] {response.message}")
                        elif response.action == "tdd_green_complete":
                            # Automatically continue to REFACTOR phase
                            response = self._respond_with_streaming("continue")
                            if response.message:
                                self.console.print(f"[cyan]Agent:[/cyan] {response.message}")
                        elif response.action == "deep_understanding_complete":
                            # Deep understanding complete, automatically continue to next step
                            # Trigger continuation by calling respond with empty message
                            if response.message:
                                self.console.print(f"[cyan]Agent:[/cyan] {response.message}")
                            # Auto-continue by calling respond again
                            next_response = self._respond_with_streaming("")
                            if next_response.message:
                                self.console.print(f"[cyan]Agent:[/cyan] {next_response.message}")
                            # Continue loop to handle the next response
                            continue
                        elif response.action == "skill_revised":
                            # Revision complete, showing results
                            continue
                        # For other actions, just continue loop
                        continue

                # Save session after each interaction
                self._save_session()

                # Check if complete
                if response.state == ConversationState.COMPLETE:
                    self.console.print("[bold green]✓ All done![/bold green]\n")
                    return 0

            except KeyboardInterrupt:
                self.console.print("\n[yellow]Interrupted. Type /exit to quit.[/yellow]\n")
                continue
            except EOFError:
                self.console.print("\n[yellow]EOF received. Exiting...[/yellow]\n")
                return 0
            except Exception as e:
                self.console.print(f"[red]Error: {e}[/red]\n")
                logger.exception("Error in interactive CLI loop")
                continue

    def _handle_command(self, command: str) -> str:
        """Handle CLI commands.

        Args:
            command: Command string (e.g., "/help", "/exit")

        Returns:
            "exit" to exit, "continue" to continue loop, "process" to process as message
        """
        parts = command.split(" ", 1)
        cmd = parts[0].lower()

        if cmd == "/help":
            self._show_help()
            return "continue"
        elif cmd in ("/exit", "/quit", "/q"):
            # Confirm exit
            if self.session.state not in [ConversationState.COMPLETE, ConversationState.EXPLORING]:
                confirm = Prompt.ask(
                    "Exit will save your progress. Continue?",
                    choices=["yes", "no"],
                    default="yes",
                )
                if confirm.lower() != "yes":
                    return "continue"
            self._save_session()
            return "exit"
        elif cmd == "/save":
            self._save_session()
            self.console.print("[green]Session saved.[/green]\n")
            return "continue"
        elif cmd == "/state":
            self.console.print(f"[dim]Current state: {self.session.state.value}[/dim]\n")
            return "continue"
        elif cmd == "/checklist":
            self._display_checklist_status(detailed=True)
            return "continue"
        elif cmd == "/history":
            self._show_history()
            return "continue"
        elif cmd == "/clear":
            self.session = ConversationSession()
            self.console.print("[yellow]Session cleared.[/yellow]\n")
            return "continue"
        elif cmd == "/skip":
            # Skip optional steps like adding counters
            if self.session.state == ConversationState.TDD_REFACTOR_PHASE:
                # Process skip as "no" response
                return "process"  # Will process "skip" as message to agent
            else:
                self.console.print("[yellow]Nothing to skip in current state.[/yellow]\n")
                return "continue"
        else:
            # Unknown command - process as regular message
            return "process"

    def _show_help(self):
        """Display help message."""
        help_text = """
**Available Commands:**

- `/help` - Show this help message
- `/exit` or `/quit` - Exit interactive mode (saves session)
- `/save` - Save current session to disk
- `/state` - Show current workflow state
- `/checklist` - Show TDD checklist status
- `/history` - Show conversation history
- `/clear` - Clear current session (start over)
- `/skip` - Skip optional steps (e.g., adding explicit counters)

**Tips:**
- Just type naturally to chat with the agent
- The agent will guide you through skill creation
- All thinking content is shown transparently
- TDD checklist is enforced automatically
"""
        self.console.print(Panel(Markdown(help_text), title="Help", border_style="blue"))
        self.console.print()

    def _display_checklist_status(self, detailed: bool = False):
        """Display TDD checklist status."""
        checklist = self.session.checklist_state

        table = Table(title="TDD Checklist Status", show_header=True, header_style="bold")
        table.add_column("Phase", style="cyan")
        table.add_column("Item", style="white")
        table.add_column("Status", style="green")

        # RED Phase
        table.add_row(
            "RED",
            "Create pressure scenarios",
            "✓" if checklist.red_scenarios_created else "✗",
        )
        table.add_row("RED", "Run baseline tests", "✓" if checklist.baseline_tests_run else "✗")
        table.add_row(
            "RED",
            "Document baseline behavior",
            "✓" if checklist.baseline_behavior_documented else "✗",
        )
        table.add_row(
            "RED",
            "Identify rationalization patterns",
            "✓" if checklist.rationalization_patterns_identified else "✗",
        )

        # GREEN Phase
        table.add_row("GREEN", "Run tests with skill", "✓" if checklist.green_tests_run else "✗")
        table.add_row(
            "GREEN",
            "Verify compliance",
            "✓" if checklist.compliance_verified else "✗",
        )
        table.add_row(
            "GREEN",
            "Address baseline failures",
            "✓" if checklist.baseline_failures_addressed else "✗",
        )

        # REFACTOR Phase
        table.add_row(
            "REFACTOR",
            "Identify new rationalizations",
            "✓" if checklist.new_rationalizations_identified else "✗",
        )
        table.add_row(
            "REFACTOR",
            "Add explicit counters",
            "✓" if checklist.explicit_counters_added else "✗",
        )
        table.add_row(
            "REFACTOR",
            "Re-test until bulletproof",
            "✓" if checklist.retested_until_bulletproof else "✗",
        )
        table.add_row(
            "REFACTOR",
            "Build rationalization table",
            "✓" if checklist.rationalization_table_built else "✗",
        )

        # Quality Checks
        table.add_row(
            "Quality",
            "Quick reference table",
            "✓" if checklist.quick_reference_included else "✗",
        )
        table.add_row(
            "Quality",
            "Common mistakes section",
            "✓" if checklist.common_mistakes_included else "✗",
        )
        table.add_row(
            "Quality",
            "No narrative storytelling",
            "✓" if checklist.no_narrative_storytelling else "✗",
        )
        table.add_row(
            "Quality",
            "Supporting files appropriate",
            "✓" if checklist.supporting_files_appropriate else "✗",
        )

        self.console.print(table)
        self.console.print()

        if checklist.is_complete():
            self.console.print("[bold green]✓ Checklist Complete! Ready to save.[/bold green]\n")
        else:
            missing = checklist.get_missing_items()
            if missing:
                self.console.print("[yellow]Missing items:[/yellow]")
                for item in missing:
                    self.console.print(f"  - {item}")
                self.console.print()

    def _display_multi_skill_queue(self):
        """Display multi-skill queue status."""
        if not self.session.multi_skill_queue:
            return

        table = Table(title="Multi-Skill Queue", show_header=True, header_style="bold")
        table.add_column("#", style="cyan")
        table.add_column("Skill Name", style="white")
        table.add_column("Status", style="green")

        for i, skill_name in enumerate(self.session.multi_skill_queue, 1):
            status = (
                "✓ Complete"
                if i < self.session.current_skill_index + 1
                else "→ In Progress"
                if i == self.session.current_skill_index + 1
                else "○ Pending"
            )
            table.add_row(str(i), skill_name, status)

        self.console.print(table)
        self.console.print()

    def _show_history(self):
        """Show conversation history."""
        if not self.session.messages:
            self.console.print("[dim]No messages yet.[/dim]\n")
            return

        panel_content = ""
        for msg in self.session.messages[-20:]:  # Last 20 messages
            role = msg.get("role", "unknown")
            content = msg.get("content", "")
            if role == "user":
                panel_content += f"[green]You:[/green] {content[:200]}\n"
            elif role == "assistant":
                panel_content += f"[cyan]Agent:[/cyan] {content[:200]}\n"
            elif role == "thinking":
                panel_content += f"[dim italic]💭 {content[:150]}[/dim italic]\n"

        self.console.print(Panel(panel_content, title="Recent History", border_style="blue"))
        self.console.print()

    def _save_session(self):
        """Save session to file."""
        try:
            session_dict = self.session.to_dict()
            self.session_file.write_text(
                json.dumps(session_dict, indent=2, default=str), encoding="utf-8"
            )
        except Exception as e:
            logger.warning(f"Could not save session: {e}")

    def _respond_with_streaming(self, user_message: str) -> AgentResponse:
        """Get agent response with real-time thinking display.

        Uses Rich's Live display to show thinking content as it streams
        from the LLM, providing immediate feedback to the user.

        Args:
            user_message: User's input message

        Returns:
            AgentResponse with message and thinking content
        """
        # Buffer for collecting streamed thinking
        thinking_buffer = []
        display_text = Text()

        def streaming_callback(chunk: str):
            """Callback for each thinking chunk from LLM."""
            thinking_buffer.append(chunk)
            # Update display text with new content
            display_text.append(chunk, style="dim italic")

        # Set the callback on the agent
        self.agent.thinking_callback = streaming_callback

        # Use Rich Live for real-time display
        with Live(
            Panel(
                display_text,
                title="[dim]💭 Thinking...[/dim]",
                border_style="dim",
                title_align="left",
            ),
            console=self.console,
            refresh_per_second=10,  # Update 10 times per second
        ) as live:
            # Get the agent response (callback will be invoked during this)
            response = self.agent.respond(user_message, self.session, capture_thinking=True)

            # Update the live display one final time with complete thinking
            if thinking_buffer:
                complete_thinking = Text()
                for chunk in thinking_buffer:
                    complete_thinking.append(chunk, style="dim italic")
                live.update(
                    Panel(
                        complete_thinking,
                        title="[dim]💭 Thinking Complete[/dim]",
                        border_style="dim",
                        title_align="left",
                    )
                )

        # Clear the callback
        self.agent.thinking_callback = None

        return response

    def _display_response(self, response: AgentResponse):
        """Display agent response with proper formatting."""
        if response.thinking_content:
            self.console.print(
                Panel(
                    f"[dim italic]{response.thinking_content}[/dim italic]",
                    title="[dim]💭 Thinking[/dim]",
                    border_style="dim",
                    title_align="left",
                )
            )
            self.console.print()

        if response.message:
            if "**" in response.message or "```" in response.message:
                self.console.print("[cyan]Agent:[/cyan]")
                self.console.print(Markdown(response.message))
            else:
                self.console.print(f"[cyan]Agent:[/cyan] {response.message}")
            self.console.print()

    def _display_multi_choice_question(self, question, reasoning: str = "") -> str:
        """Display multi-choice question with reasoning context.

        Args:
            question: ClarifyingQuestion object with question text and options
            reasoning: Agent's reasoning/thinking about why this question matters

        Returns:
            User's selected answer (option ID or free-form text)
        """
        # Show reasoning panel if provided
        if reasoning:
            self.console.print(
                Panel(
                    f"[dim italic]{reasoning}[/dim italic]",
                    title="[dim]💭 Thinking[/dim]",
                    border_style="dim",
                    title_align="left",
                )
            )
            self.console.print()

        # Display question
        self.console.print(f"\n[cyan]Agent:[/cyan] {question.question}")

        # Display context if available
        if hasattr(question, "context") and question.context:
            self.console.print(f"[dim]{question.context}[/dim]\n")
        elif hasattr(question, "description") and question.description:
            self.console.print(f"[dim]{question.description}[/dim]\n")

        # Show options
        if hasattr(question, "options") and question.options:
            for opt in question.options:
                label = f"[{opt.id}] {opt.label}"
                if hasattr(opt, "description") and opt.description:
                    label += f" - {opt.description}"
                self.console.print(f"  {label}")

            # Get user input
            valid_ids = [opt.id for opt in question.options]
            allows_multiple = getattr(question, "allows_multiple", False)

            if allows_multiple:
                choice = Prompt.ask("Your choice(s)", default=valid_ids[0])
                return ", ".join([c.strip() for c in choice.split(",")])
            else:
                # Add skip as an option for yes/no questions
                if len(valid_ids) == 2 and any(
                    k in question.question.lower() for k in ["yes", "no", "should", "add"]
                ):
                    valid_ids.append("skip")
                return Prompt.ask("Your choice", choices=valid_ids, default=valid_ids[0])
        else:
            # Free-form question
            return Prompt.ask("Your answer")


def interactive_skill_cli(args) -> int:
    """CLI entrypoint for interactive mode.

    Args:
        args: argparse.Namespace with config, skills_root, user_id, model

    Returns:
        Exit code (0 for success, 1 for error)
    """
    from ..llm import FleetConfigError, load_fleet_config
    from ..taxonomy.manager import TaxonomyManager

    try:
        # Load config
        config = load_fleet_config(Path(args.config))

        # Create taxonomy manager
        taxonomy = TaxonomyManager(Path(args.skills_root))

        # Create and run interactive CLI
        cli = InteractiveSkillCLI(
            taxonomy_manager=taxonomy,
            config=config,
            skills_root=Path(args.skills_root),
            user_id=args.user_id,
        )

        return cli.run()

    except FleetConfigError as e:
        print(f"Config error: {e}", file=sys.stderr)
        return 2
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        import traceback

        traceback.print_exc()
        return 1
