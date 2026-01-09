"""Interactive onboarding CLI for collecting user responses."""

from __future__ import annotations

from rich.console import Console
from rich.prompt import Prompt


def collect_onboarding_responses() -> dict:
    """Collect user responses through interactive prompts.

    Returns:
        Dictionary containing user's role, tech_stack, common_tasks, and experience_level
    """
    console = Console()
    responses: dict = {}

    # Question 1: Role
    console.print("[bold]1. What's your primary role?[/bold]")
    roles = [
        "Frontend Developer",
        "Backend Developer",
        "Full Stack Developer",
        "Data Scientist",
        "ML Engineer",
        "DevOps/SRE",
        "Product Manager",
        "Other",
    ]

    for i, role in enumerate(roles, 1):
        console.print(f"  {i}. {role}")

    role_choice = Prompt.ask("Choose", choices=[str(i) for i in range(1, len(roles) + 1)])
    responses["role"] = roles[int(role_choice) - 1].lower().replace(" ", "_").replace("/", "_")

    # Question 2: Tech Stack
    console.print("\n[bold]2. Which technologies do you work with?[/bold]")
    console.print("(Enter numbers separated by commas, e.g., 1,3,5)")

    techs = [
        "JavaScript/TypeScript",
        "Python",
        "Java",
        "Go",
        "Rust",
        "React",
        "Vue",
        "Node.js",
        "Django/Flask",
        "PostgreSQL",
        "MongoDB",
        "Docker",
        "Kubernetes",
        "AWS",
        "Azure",
    ]

    for i, tech in enumerate(techs, 1):
        console.print(f"  {i}. {tech}")

    tech_choices = Prompt.ask("Choose (comma-separated)")
    selected_techs = [
        techs[int(choice.strip()) - 1]
        for choice in tech_choices.split(",")
        if choice.strip().isdigit() and 1 <= int(choice.strip()) <= len(techs)
    ]
    responses["tech_stack"] = selected_techs

    # Question 3: Common Tasks
    console.print("\n[bold]3. What tasks do you perform most often?[/bold]")
    console.print("(Enter numbers separated by commas)")

    tasks = [
        "Building new features",
        "Debugging issues",
        "Code review",
        "Performance optimization",
        "Writing tests",
        "Documentation",
        "Data analysis",
        "API design",
        "Infrastructure setup",
    ]

    for i, task in enumerate(tasks, 1):
        console.print(f"  {i}. {task}")

    task_choices = Prompt.ask("Choose (comma-separated)")
    selected_tasks = [
        tasks[int(choice.strip()) - 1]
        for choice in task_choices.split(",")
        if choice.strip().isdigit() and 1 <= int(choice.strip()) <= len(tasks)
    ]
    responses["common_tasks"] = selected_tasks

    # Question 4: Experience Level
    console.print("\n[bold]4. What's your experience level?[/bold]")
    levels = ["Junior", "Mid-level", "Senior", "Lead/Principal"]

    for i, level in enumerate(levels, 1):
        console.print(f"  {i}. {level}")

    level_choice = Prompt.ask("Choose", choices=[str(i) for i in range(1, len(levels) + 1)])
    responses["experience_level"] = levels[int(level_choice) - 1].lower()

    return responses
