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
    try:
        from openinference.instrumentation.openai import OpenAIInstrumentor
    except ImportError as e:
        raise ImportError(
            "OpenAI instrumentation needs to be installed. "
            'Please install it via `pip install "atla-insights[openai]"`.'
        ) from e

    openai_instrumentor = OpenAIInstrumentor()

    return ATLA_INSTANCE.instrument_service(
        service="openai",
        instrumentors=[openai_instrumentor],
    )


def uninstrument_openai() -> None:
    """Uninstrument the OpenAI LLM provider."""
    return ATLA_INSTANCE.uninstrument_service("openai")
