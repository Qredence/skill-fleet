from __future__ import annotations

from skill_fleet.api.utils.draft_save import (
    _extract_named_file_code_blocks,
    _extract_usage_example_code_blocks,
    _safe_single_filename,
)


def test_safe_single_filename_rejects_unsafe_values():
    assert _safe_single_filename("") is None
    assert _safe_single_filename("../evil.txt") is None
    assert _safe_single_filename("/abs.txt") is None
    assert _safe_single_filename("nested/path.txt") is None
    assert _safe_single_filename(".hidden") is None
    assert _safe_single_filename("bad$name.txt") is None


def test_safe_single_filename_accepts_simple_values():
    assert _safe_single_filename("file.txt") == "file.txt"
    assert _safe_single_filename("file_name-1.md") == "file_name-1.md"


def test_extract_named_file_code_blocks():
    skill_md = """
## Something else

### `pytest.ini`
```ini
[pytest]
addopts = -q
```

### `bad/name`
```txt
ignore me
```

### `no-fence`
This section has no code fence.
"""
    blocks = _extract_named_file_code_blocks(skill_md)

    assert blocks == {"pytest.ini": "[pytest]\naddopts = -q\n"}


def test_extract_usage_example_code_blocks():
    skill_md = """
# Skill

## Usage Examples

```python
print("hello")
```

```sh
echo "hi"
```

## Notes
Other content.
"""
    blocks = _extract_usage_example_code_blocks(skill_md)

    assert blocks == {
        "example_1.py": 'print("hello")\n',
        "example_2.sh": 'echo "hi"\n',
    }
