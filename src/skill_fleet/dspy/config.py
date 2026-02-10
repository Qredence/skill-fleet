"""
DSPy context management and adapter utilities.

Configuration is now handled in the API lifespan (see api/lifespan.py) via
ConfigModelLoader from infrastructure.tracing.config.

Use dspy_context() for per-task configuration:
    with dspy_context(lm=custom_lm):
        result = await module.aforward(...)
"""

from __future__ import annotations

import os
from contextlib import contextmanager
from typing import TYPE_CHECKING, Any

import dspy
from dspy.adapters import ChatAdapter, JSONAdapter

if TYPE_CHECKING:
    from collections.abc import Generator


def _create_default_lm() -> dspy.LM:
    from ..common.env_utils import resolve_api_credentials

    model = os.getenv("DSPY_MODEL", "gemini/gemini-3-flash-preview")
    creds = resolve_api_credentials(prefer_litellm=True)
    kwargs: dict[str, Any] = {}
    api_key = creds.get("api_key")
    if api_key:
        kwargs["api_key"] = api_key
    base_url = creds.get("base_url")
    if base_url:
        kwargs["api_base"] = base_url
        kwargs.setdefault("custom_llm_provider", "litellm_proxy")
    return dspy.LM(model=model, **kwargs)


@contextmanager
def dspy_context(
    lm: dspy.LM | None = None,
    adapter: dspy.Adapter | None = None,
    rm: dspy.Retrieve | None = None,
) -> Generator[None, None, None]:
    """
    Context manager for temporary DSPy configuration.

    Use this for scoped configuration changes, especially in async contexts
    or when you need different settings for specific operations.

    Args:
        lm: Language model override
        adapter: Adapter override
        rm: Retriever override

    Example:
        >>> with dspy_context(lm=fast_lm):
        ...     result = await module.aforward(...)

    """
    with dspy.context(
        lm=lm or dspy.settings.lm or _create_default_lm(),
        adapter=adapter or dspy.settings.adapter or ChatAdapter(),
        rm=rm or dspy.settings.rm,
    ):
        yield


def create_adapter(adapter_type: str = "chat", **kwargs) -> dspy.Adapter:
    """
    Create a DSPy adapter by type.

    Args:
        adapter_type: Type of adapter ('chat', 'json', 'xml')
        **kwargs: Additional adapter-specific arguments

    Returns:
        Configured adapter instance

    Example:
        >>> adapter = create_adapter("json", use_native_function_calling=True)

    """
    adapters = {
        "chat": ChatAdapter,
        "json": JSONAdapter,
    }

    adapter_class = adapters.get(adapter_type.lower(), ChatAdapter)
    return adapter_class(**kwargs)


def get_default_adapter() -> dspy.Adapter:
    """Get the default adapter from configuration."""
    return dspy.settings.adapter or ChatAdapter()


# Removed functions (use ConfigModelLoader from infrastructure.tracing.config instead):
# - configure_dspy() - use api/lifespan.py initialization
# - get_task_lm() - use ConfigModelLoader.get_lm()
# - DSPyConfig class - singleton pattern no longer needed
