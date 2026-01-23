"""
Compatibility shims for skill-fleet restructure migration.

This module provides __getattr__ forwarding from old import paths to new locations.
All forwarders emit DeprecationWarning to encourage migration to new paths.

Usage:
    # Old import (deprecated, will still work during migration)
    from skill_fleet.core.dspy import SkillCreationProgram

    # New import (preferred)
    from skill_fleet.dspy.programs import SkillCreationProgram

Migration Timeline:
    - Phase 0.5: Shims created (current)
    - Phase 7: Shims removed after all imports updated

To find deprecated imports in your code:
    python -W default::DeprecationWarning -c "from skill_fleet.core import ..."
"""

from skill_fleet.compat.deprecation import emit_deprecation_warning

__all__ = ["emit_deprecation_warning"]
