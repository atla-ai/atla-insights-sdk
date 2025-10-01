"""Anthropic LLM provider instrumentation."""

from typing import ContextManager

from atla_insights.main import ATLA_INSTANCE
from atla_insights.suppression import NoOpContextManager, is_instrumentation_suppressed


def instrument_anthropic() -> ContextManager[None]:
    """Instrument the Anthropic LLM provider.

    This function creates a context manager that instruments the Anthropic LLM provider,
    within its context.

    ```py
    from atla_insights import instrument_anthropic

    with instrument_anthropic():
        # My Anthropic code here
    ```

    :return (ContextManager[None]): A context manager that instruments Anthropic.
    """
    if is_instrumentation_suppressed():
        return NoOpContextManager()

    from atla_insights.llm_providers.instrumentors.anthropic import (
        AtlaAnthropicInstrumentor,
    )

    anthropic_instrumentor = AtlaAnthropicInstrumentor()

    return ATLA_INSTANCE.instrument_service(
        service=AtlaAnthropicInstrumentor.name,
        instrumentors=[anthropic_instrumentor],
    )


def uninstrument_anthropic() -> None:
    """Uninstrument the Anthropic LLM provider."""
    if is_instrumentation_suppressed():
        return

    from atla_insights.llm_providers.instrumentors.anthropic import (
        AtlaAnthropicInstrumentor,
    )

    return ATLA_INSTANCE.uninstrument_service(AtlaAnthropicInstrumentor.name)
