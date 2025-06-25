"""Google GenAI LLM provider instrumentation."""

from typing import ContextManager

from atla_insights.main import ATLA_INSTANCE


def instrument_google_genai() -> ContextManager[None]:
    """Instrument the Google GenAI LLM provider.

    This function creates a context manager that instruments the Google GenAI LLM
    provider, within its context.

    ```py
    from atla_insights import instrument_google_genai

    with instrument_google_genai():
        # My Google GenAI code here
    ```

    :return (ContextManager[None]): A context manager that instruments Google GenAI.
    """
    from atla_insights.llm_providers.instrumentors.google_genai import (
        AtlaGoogleGenAIInstrumentor,
    )

    google_genai_instrumentor = AtlaGoogleGenAIInstrumentor()

    return ATLA_INSTANCE.instrument_service(
        service=AtlaGoogleGenAIInstrumentor.name,
        instrumentors=[google_genai_instrumentor],
    )


def uninstrument_google_genai() -> None:
    """Uninstrument the Google GenAI LLM provider."""
    from atla_insights.llm_providers.instrumentors.google_genai import (
        AtlaGoogleGenAIInstrumentor,
    )

    return ATLA_INSTANCE.uninstrument_service(AtlaGoogleGenAIInstrumentor.name)
