"""LiteLLM integration."""

import json
import logging
import time
from typing import Collection, Optional

from opentelemetry import context

from atla_insights.constants import OTEL_MODULE_NAME

try:
    import litellm
    from litellm.integrations.opentelemetry import OpenTelemetry
    from litellm.proxy._types import SpanAttributes
except ImportError as e:
    raise ImportError(
        "Litellm needs to be installed. "
        'Please install it via `pip install "atla-insights[litellm]"`.'
    ) from e

from opentelemetry.instrumentation.instrumentor import (  # type: ignore[attr-defined]
    BaseInstrumentor,
)
from opentelemetry.trace import SpanKind, Status, StatusCode, Tracer

logger = logging.getLogger(__name__)


# TODO(mathias): This can be re-worked to be based off OpenInference instrumentation.
class AtlaLiteLLMOpenTelemetry(OpenTelemetry):
    """An Atla LiteLLM OpenTelemetry integration."""

    def __init__(self, tracer: Tracer) -> None:
        """Initialize the Atla LiteLLM OpenTelemetry integration."""
        self.config = {}
        self.tracer = tracer
        self.callback_name = OTEL_MODULE_NAME
        self.span_kind = SpanKind
        self.message_logging = True

    def _set_attributes_atla(self, span, kwargs, response_obj) -> None:
        # Set LiteLLM otel attributes
        self.set_attributes(span, kwargs, response_obj)

        # Set Atla-specific attributes
        self.safe_set_attribute(
            span=span,
            key="atla.instrumentation.name",
            value="litellm",
        )

        # Set tool calls for assistant messages in the request
        if messages := kwargs.get("messages"):
            for idx, prompt in enumerate(messages):
                if tool_calls := prompt.get("tool_calls"):
                    self.safe_set_attribute(
                        span=span,
                        key=f"{SpanAttributes.LLM_PROMPTS.value}.{idx}.tool_calls",
                        value=json.dumps(tool_calls),
                    )

        # Set tool call IDs (if present) in a tool call response
        if response_obj is not None:
            if response_obj.get("choices"):
                for idx, choice in enumerate(response_obj.get("choices")):
                    if message := choice.get("message"):
                        if tool_calls := message.get("tool_calls"):
                            for idx, tool_call in enumerate(tool_calls):
                                if tool_call_id := tool_call.get("id"):
                                    self.safe_set_attribute(
                                        span=span,
                                        key=f"{SpanAttributes.LLM_COMPLETIONS.value}.{idx}.function_call.id",
                                        value=tool_call_id,
                                    )

    def _handle_sucess(self, kwargs, response_obj, start_time, end_time) -> None:
        self._add_dynamic_span_processor_if_needed(kwargs)

        span = self.tracer.start_span(
            name="litellm_request",
            start_time=self._to_ns(start_time),
            context=context.get_current(),
        )
        span.set_status(Status(StatusCode.OK))
        self._set_attributes_atla(span, kwargs, response_obj)
        self.set_raw_request_attributes(span, kwargs, response_obj)

        span.end(end_time=self._to_ns(end_time))

    def _handle_failure(self, kwargs, response_obj, start_time, end_time) -> None:
        span = self.tracer.start_span(
            name="litellm_request",
            start_time=self._to_ns(start_time),
            context=context.get_current(),
        )
        span.set_status(Status(StatusCode.ERROR))
        self._set_attributes_atla(span, kwargs, response_obj)
        span.end(end_time=self._to_ns(end_time))


class AtlaLiteLLMIntrumentor(BaseInstrumentor):
    """Atla instrumentor for LitelLLM."""

    atla_otel_logger: Optional[AtlaLiteLLMOpenTelemetry] = None
    name = "litellm"

    def __init__(self, tracer: Tracer) -> None:
        """Initialize the Atla LiteLLM instrumentor."""
        self.tracer = tracer

    def instrumentation_dependencies(self) -> Collection[str]:
        """Get the dependencies for the Litellm instrumentor."""
        return ("litellm >= 1.72.0",)

    def _instrument(self) -> None:
        if any(
            isinstance(callback, AtlaLiteLLMOpenTelemetry)
            for callback in litellm.callbacks
        ):
            logger.warning("Attempting to instrument already instrumented litellm")
            return

        self.atla_otel_logger = AtlaLiteLLMOpenTelemetry(tracer=self.tracer)
        litellm.callbacks.append(self.atla_otel_logger)

    def _uninstrument(self) -> None:
        if self.atla_otel_logger is None:
            logger.warning("Attempting to uninstrument not instrumented litellm")
            return

        # Wait for existing Atla callbacks to trigger before removing them.
        time.sleep(0.001)

        if self.atla_otel_logger in litellm.callbacks:
            litellm.callbacks.remove(self.atla_otel_logger)

        if self.atla_otel_logger in litellm.success_callback:
            litellm.success_callback.remove(self.atla_otel_logger)

        if self.atla_otel_logger in litellm.failure_callback:
            litellm.failure_callback.remove(self.atla_otel_logger)

        if self.atla_otel_logger in litellm.service_callback:
            litellm.service_callback.remove(self.atla_otel_logger)
