"""Instrumentation suppression functionality."""

from contextlib import contextmanager
from typing import Generator

from atla_insights.context import suppress_instrumentation_var


def is_instrumentation_suppressed() -> bool:
    """Check if Atla Insights instrumentation is currently suppressed.

    :return (bool): True if instrumentation is suppressed, False otherwise.
    """
    return suppress_instrumentation_var.get()


@contextmanager
def suppress_instrumentation() -> Generator[None, None, None]:
    """Context manager to suppress all Atla Insights instrumentation.

    When active, all Atla Insights functionality becomes stubs that do nothing.

    This includes:
    - LLM provider instrumentations
    - Framework instrumentations
    - Custom decorators (@instrument, @tool)
    - Marking functions (mark_success, mark_failure)
    - Metadata and custom metrics functions

    ```py
    from atla_insights import suppress_instrumentation

    with suppress_instrumentation():
        # All Atla Insights calls here will be no-ops
        instrument_openai()  # Does nothing
        with instrument_openai():  # Context manager does nothing
            # OpenAI calls here won't be instrumented by Atla
            pass
    ```
    """
    from atla_insights.main import ATLA_INSTANCE

    suppress_instrumentation_var.set(True)

    try:
        for instrumentors in ATLA_INSTANCE._active_instrumentors.values():
            for instrumentor in instrumentors:
                instrumentor.uninstrument()

        yield

    finally:
        enable_instrumentation()


def enable_instrumentation() -> None:
    """Enable Atla Insights instrumentation."""
    from atla_insights.main import ATLA_INSTANCE

    suppress_instrumentation_var.set(False)

    for instrumentors in ATLA_INSTANCE._active_instrumentors.values():
        for instrumentor in instrumentors:
            instrumentor.instrument()


class NoOpContextManager:
    """A no-op context manager returned when instrumentation is suppressed."""

    def __enter__(self) -> None:
        """Enter the context manager."""
        return None

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Exit the context manager."""
        pass
