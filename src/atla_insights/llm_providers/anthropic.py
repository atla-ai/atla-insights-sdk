"""Anthropic LLM provider instrumentation."""

from typing import ContextManager

from atla_insights.main import ATLA_INSTANCE


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
    try:
        from openinference.instrumentation.anthropic import AnthropicInstrumentor
    except ImportError as e:
        raise ImportError(
            "Anthropic instrumentation needs to be installed. "
            'Please install it via `pip install "atla-insights[anthropic]"`.'
        ) from e

    anthropic_instrumentor = AnthropicInstrumentor()

    return ATLA_INSTANCE.instrument_service(
        service="anthropic",
        instrumentors=[anthropic_instrumentor],
    )


def uninstrument_anthropic() -> None:
    """Uninstrument the Anthropic LLM provider."""
    return ATLA_INSTANCE.uninstrument_service("anthropic")
