"""Bedrock LLM provider instrumentation."""

from typing import ContextManager

from atla_insights.main import ATLA_INSTANCE


def instrument_bedrock() -> ContextManager[None]:
    """Instrument the Bedrock LLM provider.

    This function creates a context manager that instruments the Bedrock LLM provider,
    within its context.

    ```py
    from atla_insights import instrument_bedrock

    with instrument_bedrock():
        # My Bedrock code here
    ```

    :return (ContextManager[None]): A context manager that instruments Bedrock.
    """
    try:
        from openinference.instrumentation.bedrock import BedrockInstrumentor
    except ImportError as e:
        raise ImportError(
            "Bedrock instrumentation needs to be installed. "
            'Please install it via `pip install "atla-insights[bedrock]"`.'
        ) from e

    bedrock_instrumentor = BedrockInstrumentor()

    return ATLA_INSTANCE.instrument_service(
        service="bedrock",
        instrumentors=[bedrock_instrumentor],
    )


def uninstrument_bedrock() -> None:
    """Uninstrument the Bedrock LLM provider."""
    return ATLA_INSTANCE.uninstrument_service("bedrock")
