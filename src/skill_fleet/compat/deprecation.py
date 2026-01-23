"""Deprecation warning utilities for migration compatibility."""

from __future__ import annotations

import warnings
from functools import lru_cache
from typing import Any


@lru_cache(maxsize=256)
def _warned_once(old_path: str, new_path: str) -> bool:
    """Track warnings to emit only once per import path."""
    return True


def emit_deprecation_warning(
    old_path: str,
    new_path: str,
    removal_version: str = "1.0.0",
    stacklevel: int = 3,
) -> None:
    """
    Emit a deprecation warning for old import paths.

    Args:
        old_path: The deprecated import path (e.g., 'skill_fleet.core.dspy')
        new_path: The new import path (e.g., 'skill_fleet.dspy')
        removal_version: Version when old path will be removed
        stacklevel: How many levels up to show in warning (default 3 for __getattr__)

    """
    # Only warn once per unique path combination
    cache_key = f"{old_path}:{new_path}"
    if _warned_once(cache_key, cache_key):
        warnings.warn(
            f"Importing from '{old_path}' is deprecated. "
            f"Use '{new_path}' instead. "
            f"This import path will be removed in version {removal_version}.",
            DeprecationWarning,
            stacklevel=stacklevel,
        )


def create_module_getattr(
    module_name: str,
    attr_mapping: dict[str, tuple[str, str]],
    passthrough_attrs: set[str] | None = None,
) -> Any:
    """
    Create a __getattr__ function for module-level attribute forwarding.

    Args:
        module_name: The current module name (e.g., 'skill_fleet.core.dspy')
        attr_mapping: Dict mapping attr names to (new_module, new_attr) tuples
        passthrough_attrs: Attrs to pass through without warning (e.g., __all__)

    Returns:
        A __getattr__ function suitable for module-level use

    Example:
        # In skill_fleet/core/dspy/__init__.py
        __getattr__ = create_module_getattr(
            'skill_fleet.core.dspy',
            {
                'SkillCreationProgram': ('skill_fleet.dspy.programs', 'SkillCreationProgram'),
            }
        )

    """
    passthrough = passthrough_attrs or set()

    def __getattr__(name: str) -> Any:  # noqa: N807
        if name in passthrough:
            raise AttributeError(f"module '{module_name}' has no attribute '{name}'")

        if name in attr_mapping:
            new_module, new_attr = attr_mapping[name]
            emit_deprecation_warning(
                f"{module_name}.{name}",
                f"{new_module}.{new_attr}",
            )
            # Import from new location
            import importlib

            mod = importlib.import_module(new_module)
            return getattr(mod, new_attr)

        raise AttributeError(f"module '{module_name}' has no attribute '{name}'")

    return __getattr__


def create_package_getattr(
    package_name: str,
    submodule_mapping: dict[str, str],
) -> Any:
    """
    Create a __getattr__ for package-level submodule forwarding.

    Args:
        package_name: The current package name (e.g., 'skill_fleet.core')
        submodule_mapping: Dict mapping old submodule names to new paths

    Returns:
        A __getattr__ function for package-level use

    Example:
        # In skill_fleet/core/__init__.py
        __getattr__ = create_package_getattr(
            'skill_fleet.core',
            {
                'dspy': 'skill_fleet.dspy',
                'services': 'skill_fleet.services',
            }
        )

    """

    def __getattr__(name: str) -> Any:  # noqa: N807
        if name in submodule_mapping:
            new_path = submodule_mapping[name]
            emit_deprecation_warning(
                f"{package_name}.{name}",
                new_path,
            )
            import importlib

            return importlib.import_module(new_path)

        raise AttributeError(f"module '{package_name}' has no attribute '{name}'")

    return __getattr__
