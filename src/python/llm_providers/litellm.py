"""Litellm LLM provider instrumentation."""

from typing import ContextManager

from atla_insights.main import ATLA_INSTANCE
from atla_insights.suppression import NoOpContextManager, is_instrumentation_suppressed


def instrument_litellm() -> ContextManager[None]:
    """Instrument the Litellm LLM provider.

    This function creates a context manager that instruments the Litellm LLM provider,
    within its context.

    ```py
    from atla_insights import instrument_litellm

    with instrument_litellm():
        # My Litellm code here
    ```

    :return (ContextManager[None]): A context manager that instruments Litellm.
    """
    if is_instrumentation_suppressed():
        return NoOpContextManager()

    from atla_insights.llm_providers.instrumentors.litellm import AtlaLiteLLMIntrumentor

    # Create an instrumentor for Litellm.
    litellm_instrumentor = AtlaLiteLLMIntrumentor(tracer=ATLA_INSTANCE.get_tracer())

    return ATLA_INSTANCE.instrument_service(
        service=AtlaLiteLLMIntrumentor.name,
        instrumentors=[litellm_instrumentor],
    )


def uninstrument_litellm() -> None:
    """Uninstrument the Litellm LLM provider."""
    if is_instrumentation_suppressed():
        return

    from atla_insights.llm_providers.instrumentors.litellm import AtlaLiteLLMIntrumentor

    return ATLA_INSTANCE.uninstrument_service(AtlaLiteLLMIntrumentor.name)
