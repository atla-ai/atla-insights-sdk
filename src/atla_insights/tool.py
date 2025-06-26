"""Tool instrumentation."""

import inspect
from functools import wraps
from typing import Any, Callable

from openinference.instrumentation import safe_json_dumps
from openinference.semconv.trace import (
    OpenInferenceMimeTypeValues,
    OpenInferenceSpanKindValues,
    SpanAttributes,
)
from opentelemetry import trace as trace_api

from atla_insights.main import ATLA_INSTANCE


def tool(func: Callable[..., Any]) -> Callable[..., Any]:
    """Instrument a function-based LLM tool.

    This decorator instruments a function-based LLM tool to automatically
    capture the tool invocation parameters and output value.

    Args:
        func (Callable[..., Any]): The function to instrument.

    Returns:
        Callable[..., Any]: The wrapped function.
    """
    tracer = ATLA_INSTANCE.tracer

    if tracer is None:
        raise ValueError("Atla insights must be configured before instrumenting tools.")

    @wraps(func)
    def wrapper(*args, **kwargs) -> Any:
        with tracer.start_as_current_span(
            func.__name__,
            attributes={
                SpanAttributes.OPENINFERENCE_SPAN_KIND: OpenInferenceSpanKindValues.TOOL.value,  # noqa: E501
                SpanAttributes.TOOL_NAME: func.__name__,
                SpanAttributes.INPUT_MIME_TYPE: OpenInferenceMimeTypeValues.JSON.value,
                SpanAttributes.OUTPUT_MIME_TYPE: OpenInferenceMimeTypeValues.TEXT.value,
            },
            record_exception=False,
            set_status_on_exception=False,
        ) as span:
            if func.__doc__:
                span.set_attribute(SpanAttributes.TOOL_DESCRIPTION, func.__doc__)

            func_parameters = inspect.signature(func).bind(*args, **kwargs).arguments
            invocation_parameters = {
                k: v for k, v in func_parameters.items() if k not in {"self", "cls"}
            }

            span.set_attribute(
                SpanAttributes.INPUT_VALUE, safe_json_dumps(invocation_parameters)
            )
            if invocation_parameters:
                span.set_attribute(
                    SpanAttributes.TOOL_PARAMETERS, safe_json_dumps(invocation_parameters)
                )

            try:
                result = func(*args, **kwargs)
            except Exception as exception:
                span.set_status(
                    trace_api.Status(trace_api.StatusCode.ERROR, str(exception))
                )
                span.record_exception(exception)
                raise

            span.set_status(trace_api.StatusCode.OK)

            if result is not None:
                span.set_attribute(SpanAttributes.OUTPUT_VALUE, str(result))

        return result

    return wrapper
