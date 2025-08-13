"""OpenAI agents instrumentation."""

from typing import Any

from wrapt import wrap_function_wrapper

try:
    from agents import set_trace_processors
    from openinference.instrumentation.openai_agents import OpenAIAgentsInstrumentor
    from openinference.semconv.trace import SpanAttributes
except ImportError as e:
    raise ImportError(
        "OpenAI agents instrumentation needs to be installed. "
        'Please install it via `pip install "atla-insights[openai-agents]"`.'
    ) from e


def _get_attributes_from_function_span_data(
    wrapped: Any, instance: Any, args: Any, kwargs: Any
) -> Any:
    """Wrap the _get_attributes_from_function_span_data function to add tool params."""
    # Yield from the original instrumentation function.
    yield from wrapped(*args, **kwargs)

    # Get the tool parameters from the obj.input field.
    obj = args[0]
    if obj.input:
        yield SpanAttributes.TOOL_PARAMETERS, obj.input


class AtlaOpenAIAgentsInstrumentor(OpenAIAgentsInstrumentor):
    """Atla OpenAI Agents SDK instrumentor class."""

    name = "openai-agents"

    def _instrument(self, **kwargs: Any) -> None:
        wrap_function_wrapper(
            "openinference.instrumentation.openai_agents._processor",
            "_get_attributes_from_function_span_data",
            _get_attributes_from_function_span_data,
        )
        super()._instrument(**kwargs)

    def _uninstrument(self, **kwargs: Any) -> None:
        set_trace_processors([])
