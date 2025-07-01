"""SmolAgents instrumentation."""

from typing import Any, Callable, Iterator, Mapping, Tuple

from opentelemetry import context as context_api
from opentelemetry import trace as trace_api
from wrapt import wrap_function_wrapper

try:
    from openinference.instrumentation import safe_json_dumps
    from openinference.instrumentation.context_attributes import (
        get_attributes_from_context,
    )
    from openinference.instrumentation.smolagents import SmolagentsInstrumentor
    from openinference.instrumentation.smolagents._wrappers import (
        _bind_arguments,
        _get_input_value,
        _output_value_and_mime_type_for_tool_span,
        _strip_method_args,
    )
    from openinference.semconv.trace import OpenInferenceSpanKindValues, SpanAttributes
    from smolagents import Tool
except ImportError as e:
    raise ImportError(
        "SmolAgents instrumentation needs to be installed. "
        'Please install it via `pip install "atla-insights[smolagents]"`.'
    ) from e


def _tools(tool: "Tool") -> Iterator[Tuple[str, Any]]:
    if tool_name := getattr(tool, "name", None):
        yield SpanAttributes.TOOL_NAME, tool_name
    if tool_description := getattr(tool, "description", None):
        yield SpanAttributes.TOOL_DESCRIPTION, tool_description


def _tool_parameters(
    wrapped: Callable[..., Any],
    *args: Any,
    **kwargs: Any,
) -> Iterator[Tuple[str, Any]]:
    """Get the tool parameters from the wrapped function."""
    arguments = _bind_arguments(wrapped, *args, **kwargs)
    arguments = _strip_method_args(arguments)

    # Remove SmolAgents-specific arguments.
    if "sanitize_inputs_outputs" in arguments:
        del arguments["sanitize_inputs_outputs"]

    # Remove positional arguments if there are none.
    if not arguments.get("args"):
        del arguments["args"]

    # Remove keyword arguments if there are none.
    if not arguments.get("kwargs"):
        del arguments["kwargs"]
    else:
        # Unpack kwargs. The user will have passed them directly but the Tool.__call__
        # will nest them in a "kwargs" key because of its *args, **kwargs signature.
        arguments = {**arguments, **arguments.get("kwargs", {})}
        del arguments["kwargs"]

    if arguments:
        yield SpanAttributes.TOOL_PARAMETERS, safe_json_dumps(arguments)


class _ToolCallWrapper:
    def __init__(self, tracer: trace_api.Tracer) -> None:
        self._tracer = tracer

    def __call__(
        self,
        wrapped: Callable[..., Any],
        instance: Any,
        args: Tuple[Any, ...],
        kwargs: Mapping[str, Any],
    ) -> Any:
        if context_api.get_value(context_api._SUPPRESS_INSTRUMENTATION_KEY):
            return wrapped(*args, **kwargs)

        if hasattr(instance, "name"):
            span_name = instance.name
        else:
            span_name = f"{instance.__class__.__name__}"

        with self._tracer.start_as_current_span(
            span_name,
            attributes={
                SpanAttributes.OPENINFERENCE_SPAN_KIND: OpenInferenceSpanKindValues.TOOL.value,  # noqa: E501
                SpanAttributes.INPUT_VALUE: _get_input_value(wrapped, *args, **kwargs),
                **dict(_tools(instance)),
                **dict(_tool_parameters(wrapped, *args, **kwargs)),
                **dict(get_attributes_from_context()),
            },
            record_exception=False,
            set_status_on_exception=False,
        ) as span:
            try:
                response = wrapped(*args, **kwargs)
            except Exception as exception:
                span.set_status(
                    trace_api.Status(trace_api.StatusCode.ERROR, str(exception))
                )
                span.record_exception(exception)
                raise

            span.set_status(trace_api.StatusCode.OK)
            span.set_attributes(
                dict(
                    _output_value_and_mime_type_for_tool_span(
                        response=response,
                        output_type=instance.output_type,
                    )
                )
            )
        return response


class AtlaSmolAgentsInstrumentor(SmolagentsInstrumentor):
    """Atla SmolAgents SDK instrumentor class."""

    name = "smolagents"

    def _instrument(self, **kwargs: Any) -> None:
        super()._instrument(**kwargs)

        if self._original_tool_call_method is not None:
            Tool.__call__ = self._original_tool_call_method  # type: ignore[method-assign]

        wrap_function_wrapper(
            module="smolagents",
            name="Tool.__call__",
            wrapper=_ToolCallWrapper(self._tracer),
        )
