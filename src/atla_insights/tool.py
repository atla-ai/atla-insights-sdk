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


def _get_invocation_params(func: Callable[..., Any], *args, **kwargs) -> dict[str, Any]:
    """Get the invocation parameters for a function.

    :param func (Callable[..., Any]): The function to get the invocation parameters for.
    :param args (Any): The positional arguments to bind to the function.
    :param kwargs (Any): The keyword arguments to bind to the function.
    :return (dict[str, Any]): The invocation parameters.
    """
    func_parameters = inspect.signature(func).bind(*args, **kwargs)
    func_parameters.apply_defaults()
    return {
        k: v for k, v in func_parameters.arguments.items() if k not in {"self", "cls"}
    }


def tool(func: Callable[..., Any]) -> Callable[..., Any]:
    """Instrument a function-based LLM tool.

    This decorator instruments a function-based LLM tool to automatically
    capture the tool invocation parameters and output value.

    Args:
        func (Callable[..., Any]): The function to instrument.

    Returns:
        Callable[..., Any]: The wrapped function.
    """

    @wraps(func)
    def wrapper(*args, **kwargs) -> Any:
        with ATLA_INSTANCE.get_tracer().start_as_current_span(
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

            # Get & log the invocation parameters of the tool function.
            invocation_params = _get_invocation_params(func, *args, **kwargs)
            invocation_params_json = safe_json_dumps(invocation_params)

            span.set_attribute(SpanAttributes.INPUT_VALUE, invocation_params_json)
            if invocation_params:
                span.set_attribute(SpanAttributes.TOOL_PARAMETERS, invocation_params_json)

            # Execute the tool function.
            try:
                result = func(*args, **kwargs)
            except Exception as exception:
                span.set_status(
                    trace_api.Status(trace_api.StatusCode.ERROR, str(exception))
                )
                span.record_exception(exception)
                raise

            # Log the result of the tool function.
            span.set_status(trace_api.StatusCode.OK)
            if result is not None:
                span.set_attribute(SpanAttributes.OUTPUT_VALUE, str(result))

        return result

    return wrapper
