"""Pydantic AI instrumentation logic."""

from typing import ContextManager

from atla_insights.main import ATLA_INSTANCE
from atla_insights.suppression import NoOpContextManager, is_instrumentation_suppressed


def instrument_pydantic_ai() -> ContextManager[None]:
    """Instrument the Pydantic AI framework.

    This function creates a context manager that instruments the Pydantic AI framework,
    within its context.

    See [Pydantic AI docs](https://ai.pydantic.dev/) for usage details on the
    framework itself.

    ```py
    from atla_insights import instrument_pydantic_ai

    with instrument_pydantic_ai():
        # My Pydantic I code here
    ```

    :return (ContextManager[None]): A context manager that instruments Pydantic AI.
    """
    if is_instrumentation_suppressed():
        return NoOpContextManager()

    from atla_insights.frameworks.instrumentors.pydantic_ai import (
        pydantic_ai_instrumentor,
    )

    return ATLA_INSTANCE.instrument_service(
        service=pydantic_ai_instrumentor.name,
        instrumentors=[pydantic_ai_instrumentor],
    )


def uninstrument_pydantic_ai() -> None:
    """Uninstrument the Pydantic AI framework."""
    if is_instrumentation_suppressed():
        return

    from atla_insights.frameworks.instrumentors.pydantic_ai import (
        pydantic_ai_instrumentor,
    )

    return ATLA_INSTANCE.uninstrument_service(pydantic_ai_instrumentor.name)
