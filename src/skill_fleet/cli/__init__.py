"""CLI submodules for the agentic skills system."""

from .app import app


def cli_entrypoint():
    """Entry point for the CLI."""
    app()


__all__ = ["app", "cli_entrypoint"]
