"""Bedrock LLM provider instrumentation."""

from typing import ContextManager

from atla_insights.main import ATLA_INSTANCE


def instrument_bedrock() -> ContextManager[None]:
    """Context manager to instrument the Bedrock LLM provider for tracing.

    This context manager wraps the *creation* of boto3 Bedrock clients, not
    individual requests.
    You must enter this context *before* creating your boto3 Bedrock client(s) for
    instrumentation to take effect.
    Do not use this with other Bedrock-compatible clients (e.g., AnthropicBedrock);
    it is intended only for boto3.

    Example:
        ```py
        from atla_insights import instrument_bedrock
        import boto3

        with instrument_bedrock():
            client = boto3.client("bedrock-runtime")
            # All requests made with this client will be instrumented
        ```

    :return: A context manager that instruments boto3 Bedrock client creation.
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
