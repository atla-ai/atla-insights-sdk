"""Tests for utils module."""

import pytest


@pytest.mark.parametrize(
    "metadata, is_valid",
    [
        pytest.param(None, True, id="null"),
        pytest.param({"key": "value"}, True, id="valid"),
        pytest.param({"key": "value" * 100}, False, id="long values"),
        pytest.param({"key" * 100: "value"}, False, id="long keys"),
        pytest.param({f"{i}": f"{i}" for i in range(100)}, False, id="too many fields"),
    ],
)
def test_validate_metadata(metadata: dict[str, str], is_valid: bool) -> None:
    """Test validate_metadata function."""
    from src.atla_insights._utils import validate_metadata

    if is_valid:
        validate_metadata(metadata)
    else:
        with pytest.raises(ValueError):
            validate_metadata(metadata)
