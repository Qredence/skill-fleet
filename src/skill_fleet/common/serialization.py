"""Consolidated serialization utilities for Pydantic models and DSPy outputs.

This module provides unified functions for serializing Pydantic models,
dicts, and other complex objects to JSON-serializable formats.
Consolidates duplicate logic from phase2_generation.py.

Usage:
    from skill_fleet.common.serialization import serialize_pydantic_object

    # Serialize a single object
    result = serialize_pydantic_object(my_object, output_format="dict")

    # Serialize a list of objects
    results = serialize_pydantic_objects([obj1, obj2], output_format="dict")
"""

from __future__ import annotations

import json
from typing import Any

from pydantic import BaseModel


def serialize_pydantic_object(
    obj: Any, output_format: str = "dict"
) -> dict[str, Any] | list[Any] | str:
    """Serialize a Pydantic object or dict to JSON-compatible format.

    Args:
        obj: Object to serialize (Pydantic model, dict, or primitive)
        output_format: "dict" for dict output, "json" for JSON string

    Returns:
        Serialized object as dict, list, or JSON string

    Examples:
        >>> class Example(BaseModel):
        ...     name: str
        >>> obj = Example(name="test")
        >>> serialize_pydantic_object(obj, output_format="dict")
        {'name': 'test'}
        >>> serialize_pydantic_object(obj, output_format="json")
        '{"name":"test"}'
    """
    if obj is None:
        return {} if output_format == "dict" else "{}"

    # Check if object has model_dump method (Pydantic v2)
    if hasattr(obj, "model_dump"):
        serialized = obj.model_dump(mode="json", exclude_none=True)
    elif isinstance(obj, BaseModel):
        # Fallback for Pydantic v1 or older code
        serialized = obj.dict(exclude_none=True, by_alias=True)
    elif isinstance(obj, (dict, list, str, int, float, bool)):
        # Primitives are already JSON-serializable
        serialized = obj
    else:
        # Try to serialize as dict
        try:
            serialized = dict(obj)
        except (TypeError, ValueError):
            # Last resort: convert to string
            serialized = str(obj)

    if output_format == "json":
        return json.dumps(serialized, ensure_ascii=False, indent=2, default=str)

    return serialized


def serialize_pydantic_objects(
    items: list[Any], output_format: str = "dict"
) -> dict[str, Any] | list[Any] | str:
    """Serialize a list of Pydantic objects or dicts.

    Args:
        items: List of objects to serialize
        output_format: "dict" for dict output, "json" for JSON string,
                     "by_key" for dict with item keys as dict keys

    Returns:
        Serialized list or dict

    Examples:
        >>> class Item(BaseModel):
        ...     id: int
        ...     name: str
        >>> items = [Item(id=1, name="a"), Item(id=2, name="b")]
        >>> serialize_pydantic_objects(items)
        [{'id': 1, 'name': 'a'}, {'id': 2, 'name': 'b'}]
        >>> serialize_pydantic_objects(items, output_format="by_key", key_attr="id")
        {1: {'id': 1, 'name': 'a'}, 2: {'id': 2, 'name': 'b'}}
    """
    if not items:
        return {} if output_format == "by_key" else []

    # Serialize each item
    serialized_items = []
    for item in items:
        item_dict = serialize_pydantic_object(item, output_format="dict")
        serialized_items.append(item_dict)

    # Return as list
    if output_format == "json":
        return json.dumps(serialized_items, ensure_ascii=False, indent=2, default=str)
    elif output_format == "by_key":
        # Convert to dict by extracting key from each item
        result = {}
        for item_dict in serialized_items:
            # Try to find a key field
            if "id" in item_dict:
                key = item_dict["id"]
            elif "name" in item_dict:
                key = item_dict["name"]
            elif "filename" in item_dict:
                key = item_dict["filename"]
            else:
                # Use index if no key found
                key = len(result)
            result[key] = item_dict
        return result

    return serialized_items


def normalize_dict_output(
    obj: Any,
    expected_keys: list[str] | None = None,
    remove_none: bool = True,
) -> dict[str, Any]:
    """Normalize an object to dict format with optional validation.

    Args:
        obj: Object to normalize (Pydantic model, dict, etc.)
        expected_keys: List of keys that should be present (raises if missing)
        remove_none: Whether to remove None values from output

    Returns:
        Normalized dictionary

    Raises:
        ValueError: If expected_keys are provided and some are missing

    Examples:
        >>> class Example(BaseModel):
        ...     name: str
        ...     value: int | None
        >>> obj = Example(name="test", value=None)
        >>> normalize_dict_output(obj, remove_none=True)
        {'name': 'test'}
        >>> normalize_dict_output(obj, expected_keys=["name", "value"], remove_none=False)
        {'name': 'test', 'value': None}
    """
    # Convert to dict
    result = serialize_pydantic_object(obj, output_format="dict")

    if not isinstance(result, dict):
        raise ValueError(f"Cannot normalize object of type {type(obj)} to dict")

    # Validate expected keys
    if expected_keys:
        missing_keys = [k for k in expected_keys if k not in result]
        if missing_keys:
            raise ValueError(f"Missing expected keys: {missing_keys}")

    # Remove None values if requested
    if remove_none:
        result = {k: v for k, v in result.items() if v is not None}

    return result


def merge_subdirectory_files(
    *file_dicts: dict[str, Any],
    override: bool = False,
) -> dict[str, dict[str, Any]]:
    """Merge multiple subdirectory file dictionaries.

    Args:
        *file_dicts: Dicts to merge (e.g., references_files, guides_files, etc.)
        override: If True, later dicts override earlier dicts for same filenames

    Returns:
        Merged dict with subdirectory names as keys and file contents as values

    Examples:
        >>> refs = {"api.md": "API content", "patterns.md": "Patterns"}
        >>> guides = {"setup.md": "Setup content"}
        >>> merge_subdirectory_files({"references": refs, "guides": guides})
        {'references': {'api.md': 'API content', 'patterns.md': 'Patterns'},
         'guides': {'setup.md': 'Setup content'}}
    """
    merged: dict[str, dict[str, Any]] = {}

    for file_dict in file_dicts:
        for subdir_name, files in file_dict.items():
            if not isinstance(files, dict):
                continue

            if subdir_name not in merged:
                merged[subdir_name] = {}

            # Merge files for this subdirectory
            for filename, content in files.items():
                if override or filename not in merged[subdir_name]:
                    merged[subdir_name][filename] = content

    return merged


__all__ = [
    "serialize_pydantic_object",
    "serialize_pydantic_objects",
    "normalize_dict_output",
    "merge_subdirectory_files",
]
