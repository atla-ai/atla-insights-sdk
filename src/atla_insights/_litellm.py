"""LiteLLM integration."""

import json
from datetime import datetime
from typing import Any

try:
    from litellm.integrations.custom_logger import CustomLogger
    from litellm.integrations.opentelemetry import OpenTelemetry
    from litellm.proxy._types import SpanAttributes
except ImportError as e:
    raise ImportError(
        "Litellm needs to be installed in order to use the litellm integration. "
        "Please install it via `pip install litellm`."
    ) from e

from opentelemetry import trace
from opentelemetry.trace import SpanKind, Status, StatusCode


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

    def _postprocess_tool_call(self, tool_call: dict[str, Any]) -> dict[str, Any]:
        """Postprocess a tool call."""
        if function := tool_call.get("function"):
            if isinstance(function, dict) and function.get("arguments"):
                function["arguments"] = json.dumps(function["arguments"])
        return tool_call

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
                    tool_calls = [
                        self._postprocess_tool_call(tool_call) for tool_call in tool_calls
                    ]
                    self.safe_set_attribute(
                        span=span,
                        key=f"{SpanAttributes.LLM_PROMPTS}.{idx}.tool_calls",
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
