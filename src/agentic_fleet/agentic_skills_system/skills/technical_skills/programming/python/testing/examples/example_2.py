from capabilities.failure_analyzer import parse_traceback

raw_error = '''Traceback (most recent call last):
  File "test_math.py", line 5, in test_add
    assert add(2, 2) == 5
AssertionError: assert 4 == 5'''

summary = parse_traceback(raw_error)
print(f'Failing File: {summary["file"]}')
print(f'Error: {summary["error_msg"]}')