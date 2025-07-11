"""Google Generative AI LLM provider instrumentation."""

from typing import ContextManager

from atla_insights.main import ATLA_INSTANCE


def instrument_google_generativeai() -> ContextManager[None]:
    """Instrument the Google Generative AI LLM provider.

    Note that the `google-generativeai` package has been deprecated in favor of
    `google-genai`, and will reach EOL on September 30, 2025.

    This instrumentation is only provided for backwards compatibility, and is **not** the
    intended way to instrument Google's Generative AI services.

    Please use `instrument_google_genai` instead.

    This function creates a context manager that instruments the Google GenerativeAI LLM
    provider, within its context.

    ```py
    from atla_insights import instrument_google_generativeai

    with instrument_google_generativeai():
        # My Google Generative AI code here
    ```

    :return (ContextManager[None]): A context manager that instruments
        Google Generative AI.
    """
    from atla_insights.llm_providers.instrumentors.google_generativeai import (
        GoogleGenerativeAIInstrumentor,
    )

    google_generativeai_instrumentor = GoogleGenerativeAIInstrumentor()

    return ATLA_INSTANCE.instrument_service(
        service=GoogleGenerativeAIInstrumentor.name,
        instrumentors=[google_generativeai_instrumentor],
    )


def uninstrument_google_generativeai() -> None:
    """Uninstrument the Google Generative AI LLM provider."""
    from atla_insights.llm_providers.instrumentors.google_generativeai import (
        GoogleGenerativeAIInstrumentor,
    )

    return ATLA_INSTANCE.uninstrument_service(GoogleGenerativeAIInstrumentor.name)
