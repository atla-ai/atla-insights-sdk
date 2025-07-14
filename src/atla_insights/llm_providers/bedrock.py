from typing import ContextManager

from atla_insights.main import ATLA_INSTANCE


def instrument_bedrock() -> ContextManager[None]:
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
    return ATLA_INSTANCE.uninstrument_service("bedrock")
