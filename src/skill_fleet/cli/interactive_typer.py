"""Interactive CLI for conversational skill creation using Typer.

Provides a modern CLI with typer and rich for conversational skill creation.
Uses DSPy MultiChainComparison and Predict modules for quality assurance.
"""

from __future__ import annotations

import logging
from pathlib import Path

import typer
from rich.console import Console
from rich.live import Live
from rich.panel import Panel
from rich.text import Text

from ..taxonomy.manager import TaxonomyManager
from .interactive_cli import InteractiveSkillCLI

logger = logging.getLogger(__name__)

app = typer.Typer(help="Skills Fleet - Interactive mode", add_completion=False)

# Module-level constants for typer.Option defaults (avoids Ruff warning)
_DEFAULT_CONFIG_PATH = Path("config/fleet_config.yaml")
_DEFAULT_SKILLS_ROOT = Path("skills")
_DEFAULT_USER_ID = "default"


# =============================================================================
# Typer CLI Commands
# =============================================================================


@app.command("chat")
def interactive_chat(
    ctx: typer.Context,
    config: Path = typer.Option(
        _DEFAULT_CONFIG_PATH,
        "--config",
        "-c",
        help="Fleet LLM config YAML",
        exists=True,
    ),
    skills_root: Path = typer.Option(
        _DEFAULT_SKILLS_ROOT,
        "--skills-root",
        "-s",
        help="Skills taxonomy root",
    ),
    user_id: str = typer.Option(
        _DEFAULT_USER_ID,
        "--user-id",
        "-u",
        help="User ID for context",
    ),
    model: str | None = typer.Option(
        None,
        "--model",
        "-m",
        help="Override default model for conversational agent",
    ),
    verbose: bool = typer.Option(
        False,
        "--verbose",
        "-v",
        help="Enable verbose output (shows reasoning thinking)",
    ),
) -> None:
    """Start interactive AI agent for skill creation (chat mode).

    The agent uses DSPy framework internally and:
    - Asks clarifying questions one at a time (brainstorming approach)
    - Detects when multiple skills are needed
    - Confirms understanding before creation (mandatory checkpoint)
    - Enforces TDD checklist before saving (mandatory)
    - Shows thinking content for transparency (use --verbose)
    - Supports multi-skill creation (one at a time, checklist for each)

    Example:
        skills-fleet chat --verbose
    """
    console = Console()

    try:
        from ..llm import FleetConfigError, load_fleet_config

        # Load config
        config_obj = load_fleet_config(config)

        # Override model if specified
        if model:
            logger.info(f"Using model override: {model}")

        # Create taxonomy manager
        taxonomy = TaxonomyManager(skills_root)

        # Create and run interactive CLI
        cli = InteractiveSkillCLI(
            taxonomy_manager=taxonomy,
            config=config_obj,
            skills_root=skills_root,
            user_id=user_id,
        )

        # Run the main loop
        exit_code = cli.run()
        raise SystemExit(exit_code)

    except FleetConfigError as e:
        console.print(f"[red]Config error: {e}[/red]")
        raise SystemExit(2) from None
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        import traceback

        traceback.print_exc()
        raise SystemExit(1) from None


@app.command("test-questions")
def test_dynamic_questions(
    ctx: typer.Context,
    task: str = typer.Option(
        ...,
        "--task",
        "-t",
        help="Task description to generate questions for",
    ),
    n_questions: int = typer.Option(
        3,
        "--n-questions",
        "-n",
        help="Number of questions to generate",
    ),
    model: str | None = typer.Option(
        None,
        "--model",
        "-m",
        help="Model to use",
    ),
) -> None:
    """Test dynamic question generation (no fallback defaults).

    Generates contextual questions based on the task description.
    Each question is dynamically generated using dspy.MultiChainComparison.

    Example:
        skills-fleet test-questions --task "Create a skill for TDD testing"
    """
    console = Console()
    console.print("[cyan]Testing dynamic question generation[/cyan]")
    console.print(f"[dim]Task: {task}[/dim]")
    console.print()

    try:
        from ..llm import build_lm_for_task, load_fleet_config
        from ..workflow.conversational_modules import GenerateQuestionModuleQA

        # Load config and build LM
        config_obj = load_fleet_config(Path("config/fleet_config.yaml"))
        lm = build_lm_for_task(config_obj, "skill_understand")

        # Configure DSPy
        import dspy
        dspy.configure(lm=lm)

        # Initialize module
        module = GenerateQuestionModuleQA(n_candidates=3)

        # Generate questions
        questions_generated = []
        collected_examples = []
        conversation_context = ""

        for i in range(n_questions):
            console.print(f"[bold]Question {i + 1}/{n_questions}[/bold]")

            result = module(
                task_description=task,
                collected_examples=collected_examples,
                conversation_context=conversation_context,
                previous_questions=questions_generated,
            )

            question = result["question"]
            reasoning = result["reasoning"]
            options = result["question_options"]

            # Display reasoning (thinking content)
            if reasoning:
                console.print(Panel(
                    f"[dim italic]{reasoning}[/dim italic]",
                    title="[dim]💭 Thinking[/dim]",
                    border_style="dim",
                    title_align="left",
                ))

            # Display question
            console.print(f"[cyan]Question:[/cyan] {question}")

            # Display options if available
            if options:
                console.print("[dim]Options:[/dim]")
                for opt in options:
                    console.print(f"  [dim]- {opt}[/dim]")

            console.print()

            # Store for context
            questions_generated.append(question)

            # Simulate an answer for next iteration context
            conversation_context += f"\nQ: {question}\nA: [User provided context]\n"

        console.print("[bold green]✓ Question generation complete[/bold green]")
        console.print(f"[dim]Generated {len(questions_generated)} unique questions[/dim]")

    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        import traceback

        traceback.print_exc()
        raise SystemExit(1) from None


@app.command("test-understanding")
def test_deep_understanding(
    ctx: typer.Context,
    task: str = typer.Option(
        ...,
        "--task",
        "-t",
        help="Task description to understand",
    ),
    n_questions: int = typer.Option(
        3,
        "--n-questions",
        "-n",
        help="Number of questions to ask",
    ),
) -> None:
    """Test deep understanding phase with contextual questions.

    Generates contextual multi-choice questions to understand:
    - User's problem (WHY do they need this?)
    - User's goals (WHAT outcomes do they want?)
    - Context and constraints

    Example:
        skills-fleet test-understanding --task "Create a skill for async testing"
    """
    console = Console()
    console.print("[cyan]Testing deep understanding phase[/cyan]")
    console.print(f"[dim]Task: {task}[/dim]")
    console.print()

    try:
        from ..llm import build_lm_for_task, load_fleet_config
        from ..workflow.conversational_modules import DeepUnderstandingModuleQA

        # Load config and build LM
        config_obj = load_fleet_config(Path("config/fleet_config.yaml"))
        lm = build_lm_for_task(config_obj, "skill_understand")

        # Configure DSPy
        import dspy
        dspy.configure(lm=lm)

        # Initialize module
        module = DeepUnderstandingModuleQA(n_candidates=3)

        # Simulate conversation
        conversation_history = []
        current_understanding = ""
        research_findings = {}
        previous_questions = []

        for i in range(n_questions):
            console.print(f"[bold]Round {i + 1}/{n_questions}[/bold]")

            result = module(
                initial_task=task,
                conversation_history=conversation_history,
                research_findings=research_findings,
                current_understanding=current_understanding,
                previous_questions=previous_questions,
            )

            reasoning = result["reasoning"]
            next_question = result["next_question"]
            readiness = result["readiness_score"]
            understanding = result["understanding_summary"]

            # Display reasoning
            if reasoning:
                console.print(Panel(
                    f"[dim italic]{reasoning}[/dim italic]",
                    title="[dim]💭 Thinking[/dim]",
                    border_style="dim",
                    title_align="left",
                ))

            # Display question
            if next_question:
                question_data = next_question
                question_text = question_data.get("question", "")
                context_text = question_data.get("context", "")
                options = question_data.get("options", [])

                if context_text:
                    console.print(f"[dim]{context_text}[/dim]\n")

                console.print(f"[cyan]Question:[/cyan] {question_text}")

                if options:
                    console.print("[dim]Options:[/dim]")
                    for opt in options:
                        label = opt.get("label", "")
                        description = opt.get("description", "")
                        if description:
                            console.print(f"  [dim]- {label}: {description}[/dim]")
                        else:
                            console.print(f"  [dim]- {label}[/dim]")

                # Add to conversation history (simulate user answer)
                previous_questions.append(question_data)
                conversation_history.append({
                    "question": question_text,
                    "answer": "[User's answer]",
                })

            # Display understanding summary
            if understanding:
                console.print("\n[dim]Current Understanding:[/dim]")
                console.print(f"[dim]{understanding}[/dim]")

            # Display readiness
            console.print(f"\n[dim]Readiness: {readiness:.2%}[/dim]")
            console.print()

            if readiness >= 0.8:
                console.print("[bold green]✓ Ready to proceed![/bold green]")
                break

        console.print("[bold green]✓ Deep understanding test complete[/bold green]")

    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        import traceback

        traceback.print_exc()
        raise SystemExit(1) from None


# =============================================================================
# Shared Utilities
# =============================================================================


class TyperInteractiveCLI(InteractiveSkillCLI):
    """Extended InteractiveSkillCLI with enhanced reasoning display."""

    def _respond_with_streaming(self, user_message: str):
        """Get agent response with real-time thinking display using Rich Live.

        Enhanced version that shows reasoning content prominently using Rich Live display.

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
                title="[bold cyan]💭 Agent Thinking (Real-time)[/bold cyan]",
                border_style="cyan",
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
                live.update(Panel(
                    complete_thinking,
                    title="[bold green]💭 Thinking Complete[/bold green]",
                    border_style="green",
                    title_align="left",
                ))

        # Clear the callback
        self.agent.thinking_callback = None

        return response


if __name__ == "__main__":
    app()
