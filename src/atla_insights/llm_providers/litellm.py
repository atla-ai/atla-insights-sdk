"""Litellm LLM provider instrumentation."""

from typing import ContextManager

from atla_insights._main import ATLA_INSTANCE


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
    from atla_insights.llm_providers.instrumentors.litellm import AtlaLiteLLMIntrumentor

    litellm_instrumentor = AtlaLiteLLMIntrumentor()

    return ATLA_INSTANCE.instrument_service(
        service=AtlaLiteLLMIntrumentor.name,
        instrumentors=[litellm_instrumentor],
    )


def uninstrument_litellm() -> None:
    """Uninstrument the Litellm LLM provider."""
    from atla_insights.llm_providers.instrumentors.litellm import AtlaLiteLLMIntrumentor

    return ATLA_INSTANCE.uninstrument_service(AtlaLiteLLMIntrumentor.name)
