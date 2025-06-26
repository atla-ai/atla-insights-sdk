"""Marking functions."""

from typing import Literal

from atla_insights.constants import SUCCESS_MARK
from atla_insights.context import root_span_var
from atla_insights.main import logger


def _mark_root_span(value: Literal[0, 1]) -> None:
    """Mark the root span in the current trace with a value."""
    if root_span := root_span_var.get():
        root_span.set_attribute(SUCCESS_MARK, value)
    else:
        raise ValueError("Atla marking can only be done within an instrumented function.")


def mark_success() -> None:
    """Mark the root span in the current trace as successful.

    This function should only be called within an instrumented function.

    ```py
    from atla_insights import mark_success

    @instrument("My Function")
    def my_function() -> str:
        mark_success()
        return "success ✅"
    ```
    """
    _mark_root_span(1)
    logger.info("Marked trace as success ✅")


def mark_failure() -> None:
    """Mark the root span in the current trace as failed.

    This function should only be called within an instrumented function.

    ```py
    from atla_insights import mark_failure

    @instrument("My Function")
    def my_function() -> str:
        mark_failure()
        return "failure ❌"
    ```
    """
    _mark_root_span(0)
    logger.info("Marked trace as failure ❌")
