"""Pydantic AI instrumentation."""

from typing import Any, Collection, Optional

try:
    from openinference.instrumentation.pydantic_ai import OpenInferenceSpanProcessor
    from pydantic_ai import Agent, InstrumentationSettings
except ImportError as e:
    raise ImportError(
        "Pydantic AI instrumentation needs to be installed. "
        'Please install it via `pip install "atla-insights[pydantic-ai]"`.'
    ) from e

from opentelemetry.instrumentation.instrumentor import (  # type: ignore[attr-defined]
    BaseInstrumentor,
)
from opentelemetry.sdk.trace import ReadableSpan

from atla_insights.main import ATLA_INSTANCE


class _AtlaOpenInferenceSpanProcessor(OpenInferenceSpanProcessor):
    """Atla extension on the OpenInference Pydantic AI span processor."""

    def on_end(self, span: ReadableSpan) -> None:
        if pydantic_ai_instrumentor.instrumentation_active:
            super().on_end(span)


class _PydanticAIInstrumentor(BaseInstrumentor):
    """Pydantic AI instrumentor class."""

    name = "pydantic-ai"

    def __init__(self) -> None:
        """Initialize instrumentor without any active instrumentation."""
        self.is_instrumented = False
        self.instrumentation_active = False

        self.original_instrument_default: Optional[InstrumentationSettings | bool] = None

    def instrumentation_dependencies(self) -> Collection[str]:
        """Return a list of python packages that the will be instrumented."""
        return ("pydantic-ai",)

    def _instrument(self, **kwargs: Any) -> None:
        if ATLA_INSTANCE.tracer_provider is None:
            raise ValueError(
                "Attempting to instrument `pydantic-ai` before configuring Atla. "
                "Please run `configure()` before instrumenting."
            )

        # Set flag so that span processor starts processing Pydantic AI spans.
        self.instrumentation_active = True

        # Change default instrumentation behavior for all agents.
        self.original_instrument_default = Agent._instrument_default
        Agent.instrument_all(True)

        # Ensure actual span processor only gets added once to the tracer provider.
        if not self.is_instrumented:
            self.is_instrumented = True
            ATLA_INSTANCE.tracer_provider._active_span_processor._span_processors = (
                _AtlaOpenInferenceSpanProcessor(),
                *ATLA_INSTANCE.tracer_provider._active_span_processor._span_processors,
            )

    def _uninstrument(self, **kwargs: Any) -> None:
        # Set flag so that span processor stops processing Pydantic AI spans.
        self.instrumentation_active = False

        # Change default instrumentation behavior for all agents.
        if self.original_instrument_default is not None:
            Agent.instrument_all(self.original_instrument_default)
            self.original_instrument_default = None


# Create stateful singleton instrumentor class.
pydantic_ai_instrumentor = _PydanticAIInstrumentor()
