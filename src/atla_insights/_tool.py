"""Tool instrumentation."""

from functools import wraps
from typing import Any, Callable

import logfire
from openinference.instrumentation import safe_json_dumps
from openinference.semconv.trace import (
    OpenInferenceMimeTypeValues,
    OpenInferenceSpanKindValues,
    SpanAttributes,
)


def _get_invocation_parameters(args: tuple[Any, ...], kwargs: dict[str, Any]) -> str:
    """Get the invocation parameters from the arguments and keyword arguments."""
    invocation_parameters: dict = {**kwargs, **dict(enumerate(args))}
    invocation_parameters = {
        k: v for k, v in invocation_parameters.items() if k not in {"self", "cls"}
    }
    return safe_json_dumps(invocation_parameters)


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
        span_name = func.__name__
        with logfire.span(span_name) as span:
            span.set_attribute(
                SpanAttributes.OPENINFERENCE_SPAN_KIND,
                OpenInferenceSpanKindValues.TOOL.value,
            )
            span.set_attribute(SpanAttributes.TOOL_NAME, func.__name__)
            span.set_attribute(SpanAttributes.TOOL_DESCRIPTION, func.__doc__)

            invocation_parameters = _get_invocation_parameters(args, kwargs)
            span.set_attribute(SpanAttributes.TOOL_PARAMETERS, invocation_parameters)
            span.set_attribute(SpanAttributes.INPUT_VALUE, invocation_parameters)
            span.set_attribute(
                SpanAttributes.INPUT_MIME_TYPE, OpenInferenceMimeTypeValues.JSON.value
            )

            result = func(*args, **kwargs)

            span.set_attribute(SpanAttributes.OUTPUT_VALUE, str(result))
            span.set_attribute(
                SpanAttributes.OUTPUT_MIME_TYPE, OpenInferenceMimeTypeValues.TEXT.value
            )

        return result

    return wrapper
