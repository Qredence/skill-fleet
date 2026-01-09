---
name: python-testing
description: Comprehensive testing skill for Python applications, supporting test
  discovery, execution, and reporting across major frameworks like pytest and unittest.
category: technical_skills/programming/python
keywords:
- python
- pytest
- unittest
- testing
- coverage
- quality-assurance
- tdd
scope: Covers Python-specific testing frameworks and runners. Does not cover UI automation
  (use Playwright/Selenium skills) or performance load testing.
see_also:
- technical_skills/programming/python/execution_environment
- technical_skills/programming/practices/test_driven_development
metadata:
  skill_id: technical_skills/programming/python/testing
  version: 1.0.0
  type: technical
  weight: medium
---

# Python Testing Skill

## Overview
The Python Testing skill provides a robust framework for discovering, executing, and analyzing tests in Python environments. It supports industry-standard tools like `pytest` and `unittest`, offering features for code coverage measurement and automated failure analysis. This skill is intended to act as the primary quality gate in automated software development lifecycles, enabling agents to verify code correctness and iteratively refine implementations based on test feedback.

## Capabilities
- **Test Discovery**: Automatically identifies test files and test cases based on standard naming conventions (e.g., `test_*.py` or `*_test.py`).
- **Test Execution**: Wraps `pytest` and `unittest` runners to execute test suites and capture structured output.
- **Coverage Analysis**: Measures statement and branch coverage using `coverage.py` to ensure comprehensive testing.
- **Failure Analysis**: Parses tracebacks and assertion errors to identify the root cause of failures, providing human-readable (and LLM-readable) summaries.
- **Mocking & Isolation**: Facilitates the use of `unittest.mock` and `pytest-mock` to isolate units of code from external dependencies.

## Dependencies
- `technical_skills/programming/python` (Parent)
- `pytest` (External Python Library)
- `coverage` (External Python Library)
- `execution_environment` (Sibling - for shell access)

## Usage Examples

### Running Tests with Pytest
```python
import subprocess

def run_project_tests(path):
    # Uses the Test Runners capability to trigger pytest
    result = subprocess.run(["pytest", path, "--json-report"], capture_output=True)
    return result.stdout
```

### Mocking an API Call
```python
from unittest.mock import MagicMock
import my_module

def test_api_integration():
    # Uses Mocking & Isolation patterns
    my_module.requests.get = MagicMock(return_value={"status": "success"})
    assert my_module.call_api() == {"status": "success"}
```