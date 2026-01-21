from skill_fleet.core.dspy.modules.hitl import _get_arg


def test_get_arg_robustness():
    """Test that _get_arg handles falsy kwargs without falling back to positional args."""

    # Case 1: Key exists in kwargs but value is empty string (The Bug Case)
    kwargs = {"key": ""}
    args = ("positional_value",)

    # Should return "" (from kwargs), NOT "positional_value" (from args)
    val = _get_arg(kwargs, args, "key", 0)
    assert val == ""

    # Case 2: Key missing from kwargs, exists in args
    kwargs = {}
    args = ("positional_value",)
    val = _get_arg(kwargs, args, "key", 0)
    assert val == "positional_value"

    # Case 3: Key missing from kwargs, missing from args
    kwargs = {}
    args = ()
    val = _get_arg(kwargs, args, "key", 0)
    assert val is None

    # Case 4: Key exists and is truthy
    kwargs = {"key": "value"}
    args = ("positional_value",)
    val = _get_arg(kwargs, args, "key", 0)
    assert val == "value"
