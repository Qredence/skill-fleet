from typing import Any
from unittest.mock import AsyncMock

import pytest

from skill_fleet.core.creator import TaxonomySkillCreator
from skill_fleet.core.models import SkillCreationResult, SkillMetadata


class _FakeTaxonomy:
    """Fake taxonomy manager for testing."""

    def __init__(self):
        self.register_calls: list[dict] = []
        self.register_ok = True

    def get_mounted_skills(self, user_id: str) -> list[Any]:
        return []

    def get_relevant_branches(self, task_description: str) -> dict[str, Any]:
        return {}

    def register_skill(
        self,
        path: str,
        metadata: dict[str, Any],
        content: str,
        evolution: dict[str, Any],
        extra_files: dict[str, Any] | None = None,
        overwrite: bool = False,
    ) -> bool:
        self.register_calls.append(
            {
                "path": path,
                "metadata": metadata,
                "content": content,
                "evolution": evolution,
                "extra_files": extra_files,
                "overwrite": overwrite,
            }
        )
        return self.register_ok


def _metadata(skill_id: str = "general/testing") -> SkillMetadata:
    return SkillMetadata(
        skill_id=skill_id,
        taxonomy_path=skill_id,
        name="testing",
        description="A skill for testing.",
        type="technical",
        weight="lightweight",
        version="1.0.0",
    )


@pytest.mark.asyncio
async def test_taxonomy_skill_creator_approved_registers_skill():
    taxonomy = _FakeTaxonomy()
    creator = TaxonomySkillCreator(taxonomy_manager=taxonomy, verbose=False)  # type: ignore[arg-type]

    creator.program.aforward = AsyncMock(  # type: ignore[valid-type]
        return_value=SkillCreationResult(
            status="completed",
            skill_content="---\nname: testing\ndescription: x\n---\n\n# Testing\n",
            metadata=_metadata("general/testing"),
            extra_files={},
        )
    )

    result = await creator.acall(
        task_description="x",
        user_context={"user_id": "u"},
        auto_approve=True,
    )

    assert result["status"] == "approved"
    assert taxonomy.register_calls
    assert taxonomy.register_calls[0]["path"] == "general/testing"


@pytest.mark.asyncio
async def test_taxonomy_skill_creator_fails_when_register_skill_fails():
    taxonomy = _FakeTaxonomy()
    taxonomy.register_ok = False
    creator = TaxonomySkillCreator(taxonomy_manager=taxonomy, verbose=False)  # type: ignore[arg-type]

    creator.program.aforward = AsyncMock(  # type: ignore[valid-type]
        return_value=SkillCreationResult(
            status="completed",
            skill_content="---\nname: testing\ndescription: x\n---\n\n# Testing\n",
            metadata=_metadata("general/testing"),
        )
    )

    result = await creator.acall(
        task_description="x",
        user_context={"user_id": "u"},
        auto_approve=True,
    )

    assert result["status"] == "failed"
    assert "registration" in (result.get("error") or "").lower()


@pytest.mark.asyncio
async def test_taxonomy_skill_creator_propagates_program_failure():
    taxonomy = _FakeTaxonomy()
    creator = TaxonomySkillCreator(taxonomy_manager=taxonomy, verbose=False)  # type: ignore[arg-type]

    creator.program.aforward = AsyncMock(  # type: ignore[valid-type]
        return_value=SkillCreationResult(status="failed", error="boom")
    )

    result = await creator.acall(
        task_description="x",
        user_context={"user_id": "u"},
        auto_approve=True,
    )

    assert result["status"] == "failed"
    assert result["error"] == "boom"
