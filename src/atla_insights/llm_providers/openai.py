"""OpenAI LLM provider instrumentation."""

from typing import ContextManager

from atla_insights.main import ATLA_INSTANCE


def instrument_openai() -> ContextManager[None]:
    """Instrument the OpenAI LLM provider.

    This function creates a context manager that instruments the OpenAI LLM provider,
    within its context.

    ```py
    from atla_insights import instrument_openai

    with instrument_openai():
        # My OpenAI code here
    ```

    :return (ContextManager[None]): A context manager that instruments OpenAI.
    """
    from atla_insights.llm_providers.instrumentors.openai import AtlaOpenAIInstrumentor

    openai_instrumentor = AtlaOpenAIInstrumentor()

    return ATLA_INSTANCE.instrument_service(
        service="openai",
        instrumentors=[openai_instrumentor],
    )


def uninstrument_openai() -> None:
    """Uninstrument the OpenAI LLM provider."""
    return ATLA_INSTANCE.uninstrument_service("openai")
