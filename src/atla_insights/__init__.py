"""Atla package for PyPI distribution."""

from logfire import instrument

from ._main import (
    configure,
    instrument_litellm,
    instrument_openai,
    mark_failure,
    mark_success,
)

__version__ = "0.0.1a5"

__all__ = [
    "configure",
    "instrument",
    "instrument_litellm",
    "instrument_openai",
    "mark_failure",
    "mark_success",
]
