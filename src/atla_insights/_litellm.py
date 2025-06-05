"""LiteLLM integration."""

import json
import logging
import time
from datetime import datetime
from typing import Collection, Optional

try:
    import litellm
    from litellm.integrations.custom_logger import CustomLogger
    from litellm.integrations.opentelemetry import OpenTelemetry
    from litellm.proxy._types import SpanAttributes
except ImportError as e:
    raise ImportError(
        "Litellm needs to be installed. "
        "Please install it via `pip install atla-insights[litellm]`."
    ) from e

from opentelemetry import trace
from opentelemetry.instrumentation.instrumentor import (  # type: ignore[attr-defined]
    BaseInstrumentor,
)
from opentelemetry.trace import SpanKind, Status, StatusCode

logger = logging.getLogger(__name__)


# TODO(mathias): This can be re-worked to be based off OpenInference instrumentation.
class AtlaLiteLLMOpenTelemetry(OpenTelemetry):
    """An Atla LiteLLM OpenTelemetry integration."""

    def __init__(self, **kwargs) -> None:
        """Initialize the Atla LiteLLM OpenTelemetry integration."""
        self.config = {}
        self.tracer = trace.get_tracer("logfire")
        self.callback_name = None
        self.span_kind = SpanKind

        CustomLogger.__init__(self, **kwargs)
        self._init_otel_logger_on_litellm_proxy()

    def _set_attributes_atla(self, span, kwargs, response_obj) -> None:
        # Set LiteLLM otel attributes
        self.set_attributes(span, kwargs, response_obj)

        # Set Atla-specific attributes
        self.safe_set_attribute(
            span=span,
            key="atla.instrumentation.name",
            value="litellm",
        )

        if messages := kwargs.get("messages"):
            for idx, prompt in enumerate(messages):
                if tool_calls := prompt.get("tool_calls"):
                    self.safe_set_attribute(
                        span=span,
                        key=f"{SpanAttributes.LLM_PROMPTS.value}.{idx}.tool_calls",
                        value=json.dumps(tool_calls),
                    )

    def _handle_sucess(self, kwargs, response_obj, start_time, end_time) -> None:
        _parent_context, parent_otel_span = self._get_span_context(kwargs)

        self._add_dynamic_span_processor_if_needed(kwargs)

        span = self.tracer.start_span(
            name=self._get_span_name(kwargs),
            start_time=self._to_ns(start_time),
            context=_parent_context,
        )
        span.set_status(Status(StatusCode.OK))
        self._set_attributes_atla(span, kwargs, response_obj)
        self.set_raw_request_attributes(span, kwargs, response_obj)

        span.end(end_time=self._to_ns(end_time))

        if parent_otel_span is not None:
            parent_otel_span.end(end_time=self._to_ns(datetime.now()))

    def _handle_failure(self, kwargs, response_obj, start_time, end_time) -> None:
        _parent_context, parent_otel_span = self._get_span_context(kwargs)

        span = self.tracer.start_span(
            name=self._get_span_name(kwargs),
            start_time=self._to_ns(start_time),
            context=_parent_context,
        )
        span.set_status(Status(StatusCode.ERROR))
        self._set_attributes_atla(span, kwargs, response_obj)
        span.end(end_time=self._to_ns(end_time))

        if parent_otel_span is not None:
            parent_otel_span.end(end_time=self._to_ns(datetime.now()))


class AtlaLiteLLMIntrumentor(BaseInstrumentor):
    """Atla instrumentor for LitelLLM."""

    atla_otel_logger: Optional[AtlaLiteLLMOpenTelemetry] = None

    def instrumentation_dependencies(self) -> Collection[str]:
        return ("litellm >= 1.72.0",)

    def _instrument(self) -> None:
        if any(
            isinstance(callback, AtlaLiteLLMOpenTelemetry)
            for callback in litellm.callbacks
        ):
            logger.warning("Attempting to instrument already instrumented litellm")
            return

        self.atla_otel_logger = AtlaLiteLLMOpenTelemetry()
        litellm.callbacks.append(self.atla_otel_logger)

    def _uninstrument(self) -> None:
        if self.atla_otel_logger is None:
            logger.warning("Attempting to uninstrument not instrumented litellm")
            return

        # Wait existing Atla callbacks to trigger before removing them.
        time.sleep(0.001)

        if self.atla_otel_logger in litellm.callbacks:
            litellm.callbacks.remove(self.atla_otel_logger)

        if self.atla_otel_logger in litellm.success_callback:
            litellm.success_callback.remove(self.atla_otel_logger)

        if self.atla_otel_logger in litellm.failure_callback:
            litellm.failure_callback.remove(self.atla_otel_logger)

        if self.atla_otel_logger in litellm.service_callback:
            litellm.service_callback.remove(self.atla_otel_logger)
