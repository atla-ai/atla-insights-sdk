"""Atla package for PyPI distribution."""

from logfire import instrument

from ._main import (
    configure,
    instrument_litellm,
    instrument_openai,
    mark_failure,
    mark_success,
)

__all__ = [
    "configure",
    "instrument",
    "instrument_litellm",
    "instrument_openai",
    "mark_failure",
    "mark_success",
]
