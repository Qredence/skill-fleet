"""
Centralized DSPy configuration for skill-fleet.

Provides a singleton configuration class, context managers, and utilities
for managing DSPy settings including LMs, adapters, and retrievers.
"""

from __future__ import annotations

import asyncio
import os
from contextlib import contextmanager
from pathlib import Path
from typing import TYPE_CHECKING

import dspy
import yaml
from dspy.adapters import ChatAdapter, JSONAdapter

if TYPE_CHECKING:
    from collections.abc import Generator


def _in_async_task() -> bool:
    try:
        return asyncio.current_task() is not None
    except RuntimeError:
        # No running event loop in this thread.
        return False


def _create_default_lm() -> dspy.LM:
    model = os.getenv("DSPY_MODEL", "gemini-3-flash-preview")
    return dspy.LM(model=model)


def get_task_lm(task: str | None = None) -> dspy.LM:
    """
    Get task-specific language model.

    Args:
        task: Task identifier (e.g., 'skill_understand', 'skill_edit')

    Returns:
        Configured LM for the task

    """
    config = DSPyConfig()
    return config.get_lm() or dspy.settings.lm or _create_default_lm()


class DSPyConfig:
    """
    Singleton for centralized DSPy configuration.

    Provides thread-safe configuration management with support for:
    - Language models (LMs)
    - Adapters (ChatAdapter, JSONAdapter, etc.)
    - Retrievers (RMs)
    - Task-specific configurations

    Example:
        >>> config = DSPyConfig()
        >>> config.configure(lm=dspy.LM("gemini/gemini-3-flash-preview"))
        >>> lm = config.get_lm()

    """

    _instance: DSPyConfig | None = None

    def __new__(cls) -> DSPyConfig:
        """Create singleton instance."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self) -> None:
        """Initialize configuration."""
        if self._initialized:
            return
        self._initialized = True
        self._lm: dspy.LM | None = None
        self._adapter: dspy.Adapter | None = None
        self._rm: dspy.Retrieve | None = None
        self._config_path: Path | None = None

    def configure(
        self,
        lm: dspy.LM | None = None,
        adapter: dspy.Adapter | None = None,
        rm: dspy.Retrieve | None = None,
        config_path: Path | str | None = None,
    ) -> None:
        """
        Configure DSPy with explicit settings.

        Args:
            lm: Language model to use
            adapter: Adapter for parsing/formatting (defaults to ChatAdapter)
            rm: Retriever model for RAG
            config_path: Path to YAML config file

        """
        if _in_async_task():
            raise RuntimeError(
                "configure_dspy()/DSPyConfig.configure() must not be called from an async task; "
                "configure globally at startup and use dspy_context(...) per-request."
            )

        if config_path:
            self._load_from_config(Path(config_path))

        if lm:
            self._lm = lm
        if adapter:
            self._adapter = adapter
        if rm:
            self._rm = rm

        # Default to ChatAdapter if no adapter set
        if self._adapter is None:
            self._adapter = ChatAdapter()

        lm_to_set = self._lm or dspy.settings.lm
        adapter_to_set = self._adapter or dspy.settings.adapter or ChatAdapter()
        rm_to_set = self._rm or dspy.settings.rm

        if lm_to_set is None:
            lm_to_set = _create_default_lm()

        dspy.configure(lm=lm_to_set, adapter=adapter_to_set, rm=rm_to_set)

    def _load_from_config(self, config_path: Path) -> None:
        """Load configuration from YAML file."""
        if not config_path.exists():
            return

        with open(config_path) as f:
            config = yaml.safe_load(f)

        if not config or "llm" not in config:
            return

        llm_config = config["llm"]
        model = llm_config.get("model", "gemini-3-flash-preview")
        temperature = llm_config.get("temperature", 1)
        max_tokens = llm_config.get("max_tokens", 4096)

        self._lm = dspy.LM(
            model=model,
            temperature=temperature,
            max_tokens=max_tokens,
            cache=llm_config.get("cache", True),
        )

    def get_lm(self) -> dspy.LM | None:
        """Get configured language model."""
        return self._lm or dspy.settings.lm

    def get_adapter(self) -> dspy.Adapter:
        """Get configured adapter."""
        return self._adapter or dspy.settings.adapter or ChatAdapter()

    def get_rm(self) -> dspy.Retrieve | None:
        """Get configured retriever."""
        return self._rm or dspy.settings.rm


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
    config = DSPyConfig()

    with dspy.context(
        lm=lm or config.get_lm() or _create_default_lm(),
        adapter=adapter or config.get_adapter(),
        rm=rm or config.get_rm(),
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
    return DSPyConfig().get_adapter()


def configure_dspy(
    config_path: Path | str | None = None,
    lm: dspy.LM | None = None,
    adapter: dspy.Adapter | None = None,
) -> None:
    """
    Configure DSPy for skill-fleet.

    Call this once at application startup.

    Args:
        config_path: Path to config YAML file
        lm: Pre-configured LM (optional)
        adapter: Pre-configured adapter (optional)

    Example:
        >>> from pathlib import Path
        >>> configure_dspy(config_path=Path("config/config.yaml"))

    """
    if _in_async_task():
        raise RuntimeError(
            "configure_dspy() must not be called from an async task; configure at startup and "
            "use dspy_context(...) per-request."
        )

    config = DSPyConfig()

    # Use environment overrides
    litellm_model = os.getenv("LITELLM_MODEL")
    if lm is None and litellm_model:
        lm = dspy.LM(model=litellm_model)

    if adapter is None:
        adapter = create_adapter("chat")

    if lm is None:
        lm = dspy.settings.lm or config.get_lm() or _create_default_lm()

    config.configure(
        lm=lm,
        adapter=adapter,
        config_path=config_path,
    )
