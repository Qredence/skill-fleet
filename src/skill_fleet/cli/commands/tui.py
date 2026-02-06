"""
OpenTUI-based terminal UI for Skill Fleet.

This command is intended for local development workflows. It shells out to Bun
to run the OpenTUI React app under `cli/tui`.
"""

from __future__ import annotations

import os
import subprocess  # nosec: B404
from pathlib import Path

import typer
from rich.console import Console

console = Console()


def tui_command(ctx: typer.Context) -> None:
    """
    Launch the OpenTUI Skill Fleet TUI (dev mode).

    Requires Bun to be installed on the system.
    """
    # Best-effort repo root detection for dev environments.
    repo_root = Path(__file__).resolve().parents[4]
    tui_dir = repo_root / "cli" / "tui"

    if not tui_dir.exists():
        console.print(
            f"[red]Error:[/red] TUI directory not found at {tui_dir}. Run from the repo checkout.",
        )
        raise typer.Exit(1)

    api_url = getattr(getattr(ctx, "obj", None), "api_url", None) or os.getenv(
        "SKILL_FLEET_API_URL", "http://localhost:8000"
    )
    user_id = getattr(getattr(ctx, "obj", None), "user_id", None) or os.getenv(
        "SKILL_FLEET_USER_ID", "default"
    )

    env = dict(os.environ)
    env["SKILL_FLEET_API_URL"] = str(api_url)
    env["SKILL_FLEET_USER_ID"] = str(user_id)

    console.print(f"[dim]Launching TUI…[/dim] (API={api_url}, user={user_id})")

    try:
        node_modules_dir = tui_dir / "node_modules"
        if not node_modules_dir.is_dir():
            console.print("[dim]Installing TUI dependencies...[/dim]")
            subprocess.run(["bun", "install"], cwd=str(tui_dir), env=env, check=True)  # nosec B607,B603
        subprocess.run(["bun", "run", "dev"], cwd=str(tui_dir), env=env, check=True)  # nosec B607,B603
    except FileNotFoundError as exc:
        console.print(
            "[red]Error:[/red] Bun is not installed or not on PATH. Install Bun to run the TUI.",
        )
        raise typer.Exit(1) from exc
    except subprocess.CalledProcessError as exc:
        console.print(f"[red]Error:[/red] Failed to launch TUI (exit={exc.returncode})")
        raise typer.Exit(exc.returncode) from exc
