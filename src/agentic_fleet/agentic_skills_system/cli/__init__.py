"""CLI submodules for the agentic skills system."""

from .main import cli_entrypoint, main
from .onboarding_cli import collect_onboarding_responses

__all__ = ["collect_onboarding_responses", "cli_entrypoint", "main"]
