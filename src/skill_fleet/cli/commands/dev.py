"""CLI command for starting the API server in development mode."""

from __future__ import annotations

import os
import subprocess  # nosec B404
import sys
import time
from pathlib import Path

import httpx
import typer
from rich.console import Console

from ..client import SkillFleetClient
from ..commands.chat import chat_command
from ..utils.security import sanitize_user_id

console = Console()


def _wait_for_api_ready(url: str, timeout: float = 30.0) -> bool:
    """
    Wait for the API server to be ready (accepting requests).

    Args:
        url: The base API URL (e.g., http://127.0.0.1:8000)
        timeout: Maximum time to wait in seconds

    Returns:
        True if API is ready, False if timeout reached
    """
    start = time.time()
    health_url = f"{url}/docs"  # FastAPI docs endpoint (lightweight check)

    while time.time() - start < timeout:
        try:
            with httpx.Client(timeout=2.0) as client:
                response = client.get(health_url)
                if response.status_code == 200:
                    return True
        except (httpx.ConnectError, httpx.TimeoutException, OSError):
            time.sleep(0.5)

    return False


def _resolve_repo_root() -> Path:
    """Resolve the repository root directory."""
    return Path(__file__).resolve().parents[4]


def _derive_api_url(host: str, port: int, configured_api_url: str | None) -> str:
    """Derive the API URL, honoring configured value when provided."""
    if configured_api_url and configured_api_url != "http://localhost:8000":
        return configured_api_url

    resolved_host = host
    if host in {"0.0.0.0", "::"}:  # nosec B104
        resolved_host = "127.0.0.1"
    return f"http://{resolved_host}:{port}"


def dev_command(
    ctx: typer.Context,
    task: str | None = typer.Argument(None, help="Optional task to run immediately"),
    port: int = typer.Option(8000, "--port", "-p", help="Port to run the API server on"),
    host: str = typer.Option("127.0.0.1", "--host", help="Host to bind the API server to"),
    reload: bool = typer.Option(
        False,
        "--reload/--no-reload",
        help="Enable auto-reload on file changes (default: disabled to prevent port conflicts)",
    ),
    auto_approve: bool = typer.Option(False, "--auto-approve", help="Skip interactive prompts"),
    show_thinking: bool = typer.Option(
        True,
        "--show-thinking/--no-show-thinking",
        help="Show rationale/thinking panels when available",
    ),
    force_plain_text: bool = typer.Option(
        False,
        "--force-plain-text",
        help="Disable arrow-key dialogs and use plain-text prompts",
    ),
    fast: bool = typer.Option(
        True,
        "--fast/--slow",
        help="Use fast polling (100ms) for real-time updates",
    ),
    stream: bool = typer.Option(
        True,
        "--stream/--poll",
        help="Use streaming mode with live progress (default) or polling-only mode",
    ),
):
    """
    Start the Skill Fleet API server in development mode.

    By default, auto-reload is disabled to prevent port binding issues when files change.
    Use --reload to enable auto-reload (requires uvicorn to cleanly rebind ports).
    """
    config = ctx.obj if ctx is not None else None
    configured_api_url = getattr(config, "api_url", None)

    # Sanitize user_id from config or env var
    raw_user_id = getattr(config, "user_id", os.getenv("SKILL_FLEET_USER_ID", "default"))
    try:
        user_id = sanitize_user_id(raw_user_id)
    except ValueError as e:
        console.print(f"[bold red]Error:[/bold red] Invalid user_id: {e}", style="bold red")
        raise typer.Exit(1) from e

    api_url = _derive_api_url(host, port, configured_api_url)

    repo_root = _resolve_repo_root()

    console.print("[bold green]🚀 Starting Skill Fleet API...[/bold green]")
    console.print(f"[dim]API URL: {api_url}[/dim]")
    console.print(f"[dim]User ID: {user_id}[/dim]")
    console.print(f"[dim]Reload: {'enabled' if reload else 'disabled'}[/dim]")

    api_env = os.environ.copy()
    env_mode = api_env.get("SKILL_FLEET_ENV")
    if env_mode not in {"development", "dev"}:
        api_env["SKILL_FLEET_ENV"] = "development"
        if env_mode:
            console.print(
                f"[bold yellow]⚠️  Overriding SKILL_FLEET_ENV={env_mode} → development for dev server[/bold yellow]"
            )
        else:
            console.print("[dim]SKILL_FLEET_ENV=development[/dim]")

    api_cmd = [
        sys.executable,
        "-m",
        "uvicorn",
        "skill_fleet.api.main:app",
        "--host",
        host,
        "--port",
        str(port),
    ]
    if reload:
        api_cmd.append("--reload")
        console.print(
            "[bold yellow]⚠️  Auto-reload enabled (in-memory jobs reset on reload)[/bold yellow]"
        )
    else:
        console.print("[dim]💡 Tip: To enable auto-reload, use: skill-fleet dev --reload[/dim]")

    log_dir = repo_root / ".skill_fleet_logs"
    log_dir.mkdir(exist_ok=True)
    api_log_path = log_dir / "api-dev.log"
    api_log_handle = api_log_path.open("a", encoding="utf-8")
    console.print(f"[dim]API logs → {api_log_path}[/dim]")

    try:
        api_proc = subprocess.Popen(  # nosec B603
            api_cmd,
            cwd=repo_root,
            env=api_env,
            stdout=api_log_handle,
            stderr=api_log_handle,
        )
    except FileNotFoundError as exc:
        console.print(f"[bold red]Failed to start API server: {exc}[/bold red]")
        raise typer.Exit(code=1) from exc

    try:
        if not _wait_for_api_ready(api_url):
            console.print(
                "[bold red]API did not become ready in time. See the log for details:[/bold red]"
            )
            if api_log_path.exists():
                console.print(f"[dim]{api_log_path}[/dim]")
                try:
                    log_tail = api_log_path.read_text(encoding="utf-8").splitlines()[-40:]
                    for line in log_tail:
                        console.print(line)
                except OSError:
                    console.print("[yellow]Unable to read API log.[/yellow]")
            raise typer.Exit(code=1)

        if ctx and ctx.obj:
            ctx.obj.api_url = api_url
            ctx.obj.client = SkillFleetClient(api_url)

        chat_command(
            ctx,
            task=task,
            auto_approve=auto_approve,
            show_thinking=show_thinking,
            force_plain_text=force_plain_text,
            fast=fast,
            stream=stream,
        )
    except KeyboardInterrupt:
        console.print("\n[dim]Shutting down...[/dim]")
    finally:
        if api_proc and api_proc.poll() is None:
            api_proc.terminate()
            try:
                api_proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                api_proc.kill()
        api_log_handle.close()
