import logging

import pytest
from pydantic import BaseModel

from skill_fleet.common.utils import safe_float, safe_json_loads


class _PydanticExample(BaseModel):
    x: int
    y: str


def test_safe_json_loads_returns_dict_and_list_as_is() -> None:
    d = {"a": 1}
    lst = [1, 2, 3]

    assert safe_json_loads(d) == d
    assert safe_json_loads(lst) == lst


def test_safe_json_loads_handles_pydantic_model() -> None:
    model = _PydanticExample(x=1, y="ok")
    assert safe_json_loads(model, default={}) == {"x": 1, "y": "ok"}


def test_safe_json_loads_parses_valid_json_string() -> None:
    assert safe_json_loads('{"a": 1}', default={}) == {"a": 1}
    assert safe_json_loads("[1, 2]", default=[]) == [1, 2]


def test_safe_json_loads_invalid_json_falls_back_and_logs(caplog: pytest.LogCaptureFixture) -> None:
    caplog.set_level(logging.WARNING)
    assert safe_json_loads("{not json}", default={"fallback": True}, field_name="x") == {
        "fallback": True
    }

    messages = "\n".join(r.message for r in caplog.records)
    assert "Failed to parse JSON for field 'x'" in messages


def test_safe_json_loads_empty_and_unknown_types_fall_back(
    caplog: pytest.LogCaptureFixture,
) -> None:
    caplog.set_level(logging.WARNING)

    assert safe_json_loads("", default={"d": 1}) == {"d": 1}
    assert safe_json_loads(None, default=[]) == []
    assert safe_json_loads(123, default={"d": 2}, field_name="weird") == {"d": 2}

    messages = "\n".join(r.message for r in caplog.records)
    assert "Unexpected type for field 'weird'" in messages


def test_safe_float_handles_common_inputs() -> None:
    assert safe_float(1) == 1.0
    assert safe_float(1.5) == 1.5
    assert safe_float("2.25") == 2.25
    assert safe_float("nope", default=0.75) == 0.75
    assert safe_float(None, default=0.5) == 0.5
