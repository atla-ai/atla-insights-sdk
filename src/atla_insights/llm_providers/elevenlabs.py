"""ElevenLabs LLM provider instrumentation."""

from typing import ContextManager, cast

from opentelemetry.sdk.trace import TracerProvider

from atla_insights.main import ATLA_INSTANCE
from atla_insights.suppression import (
    NoOpContextManager,
    is_instrumentation_suppressed,
)


def instrument_elevenlabs() -> ContextManager[None]:
    """Instrument the ElevenLabs Python SDK.

    This function creates a context manager that instruments the ElevenLabs LLM
    provider, within its context.

    ```py
    from atla_insights import instrument_elevenlabs

    with instrument_elevenlabs():
        # My ElevenLabs code here
    ```

    :return (ContextManager[None]): A context manager that instruments ElevenLabs.
    """
    if is_instrumentation_suppressed():
        return NoOpContextManager()

    from atla_insights.llm_providers.instrumentors.elevenlabs import (
        AtlaElevenLabsInstrumentor,
    )

    tracer = cast(TracerProvider, ATLA_INSTANCE.tracer_provider).get_tracer(
        "openinference.instrumentation.elevenlabs"
    )
    instrumentor = AtlaElevenLabsInstrumentor(tracer=tracer)

    return ATLA_INSTANCE.instrument_service(
        service=AtlaElevenLabsInstrumentor.name,
        instrumentors=[instrumentor],
    )


def uninstrument_elevenlabs() -> None:
    """Uninstrument the ElevenLabs Python SDK."""
    if is_instrumentation_suppressed():
        return

    from atla_insights.llm_providers.instrumentors.elevenlabs import (
        AtlaElevenLabsInstrumentor,
    )

    ATLA_INSTANCE.uninstrument_service(AtlaElevenLabsInstrumentor.name)
