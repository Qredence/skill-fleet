{
    "test_id": "test_basic_wrapper_identity",
    "description": "Verify that using @functools.wraps preserves the original function name and docstring.",
    "expected_outcome": "wrapped_func.__name__ == 'original_name'",
}
