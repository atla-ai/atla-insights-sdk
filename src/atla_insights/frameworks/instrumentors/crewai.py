"""CrewAI instrumentation."""

from importlib import import_module
from typing import Any, Callable, Mapping

from opentelemetry import context as context_api
from opentelemetry import trace as trace_api
from opentelemetry.trace import Tracer
from wrapt import wrap_function_wrapper

try:
    import litellm
    from openinference.instrumentation import (
        get_attributes_from_context,
        get_output_attributes,
        safe_json_dumps,
    )
    from openinference.instrumentation.crewai import CrewAIInstrumentor
    from openinference.instrumentation.crewai._wrappers import (
        _ExecuteCoreWrapper,
        _flatten,
        _get_input_value,
        _KickoffWrapper,
    )
    from openinference.semconv.trace import OpenInferenceSpanKindValues, SpanAttributes
except ImportError as e:
    raise ImportError(
        "CrewAI instrumentation needs to be installed. "
        'Please install it via `pip install "atla-insights[crewai]"`.'
    ) from e


def _set_callbacks(
    wrapped: Callable[..., Any],
    instance: Any,
    args: tuple[Any, ...],
    kwargs: Mapping[str, Any],
) -> None:
    """Ensures Atla Insights litellm callbacks are never unintentionally overwritten."""
    if callbacks := kwargs.get("callbacks"):
        for callback in callbacks:
            if callback not in litellm.callbacks:
                litellm.callbacks.append(callback)


class _ToolUseWrapper:
    """Ensures Atla Insights tool invocation spans are correctly instrumented."""

    def __init__(self, tracer: trace_api.Tracer) -> None:
        self._tracer = tracer

    def __call__(
        self,
        wrapped: Callable[..., Any],
        instance: Any,
        args: tuple[Any, Any, Any],
        kwargs: Mapping[str, Any],
    ) -> Any:
        if context_api.get_value(context_api._SUPPRESS_INSTRUMENTATION_KEY):
            return wrapped(*args, **kwargs)

        if kwargs.get("tool") or len(args) > 1:
            tool = kwargs.get("tool") or args[1]
            span_name = tool.name
        elif instance:
            span_name = f"{instance.__class__.__name__}.{wrapped.__name__}"
        else:
            span_name = wrapped.__name__

        with self._tracer.start_as_current_span(
            span_name,
            attributes=dict(
                _flatten(
                    {
                        SpanAttributes.OPENINFERENCE_SPAN_KIND: OpenInferenceSpanKindValues.TOOL,  # noqa: E501
                        SpanAttributes.INPUT_VALUE: _get_input_value(
                            wrapped,
                            *args,
                            **kwargs,
                        ),
                    }
                )
            ),
            record_exception=False,
            set_status_on_exception=False,
        ) as span:
            if kwargs.get("tool") or len(args) > 1:
                tool = kwargs.get("tool") or args[1]

                span.set_attribute(SpanAttributes.TOOL_NAME, tool.name)
                span.set_attribute(SpanAttributes.TOOL_DESCRIPTION, tool.description)

            if kwargs.get("tool_calling") or len(args) > 2:
                tool_calling = kwargs.get("tool_calling") or args[2]
                span.set_attribute(
                    SpanAttributes.TOOL_PARAMETERS,
                    safe_json_dumps(tool_calling.arguments),
                )

            span.set_attribute("function_calling_llm", instance.function_calling_llm)
            try:
                response = wrapped(*args, **kwargs)
            except Exception as exception:
                span.set_status(
                    trace_api.Status(trace_api.StatusCode.ERROR, str(exception))
                )
                span.record_exception(exception)
                raise
            span.set_status(trace_api.StatusCode.OK)
            span.set_attributes(dict(get_output_attributes(response)))
            span.set_attributes(dict(get_attributes_from_context()))
        return response


class AtlaCrewAIInstrumentor(CrewAIInstrumentor):
    """Atla CrewAI instrumentator class."""

    name = "crewai"

    def __init__(self, tracer: Tracer) -> None:
        """Initialize the Atla CrewAI instrumentator.

        :param tracer (Tracer): The OpenTelemetry tracer to use for tracing.
        """
        super().__init__()
        self.tracer = tracer

    def _instrument(self, **kwargs: Any) -> None:
        execute_core_wrapper = _ExecuteCoreWrapper(tracer=self.tracer)
        self._original_execute_core = getattr(
            import_module("crewai").Task, "_execute_core", None
        )
        wrap_function_wrapper(
            module="crewai",
            name="Task._execute_core",
            wrapper=execute_core_wrapper,
        )

        kickoff_wrapper = _KickoffWrapper(tracer=self.tracer)
        self._original_kickoff = getattr(import_module("crewai").Crew, "kickoff", None)
        wrap_function_wrapper(
            module="crewai",
            name="Crew.kickoff",
            wrapper=kickoff_wrapper,
        )

        use_wrapper = _ToolUseWrapper(tracer=self.tracer)
        self._original_tool_use = getattr(
            import_module("crewai.tools.tool_usage").ToolUsage, "_use", None
        )
        wrap_function_wrapper(
            module="crewai.tools.tool_usage",
            name="ToolUsage._use",
            wrapper=use_wrapper,
        )

        self._original_set_callbacks = getattr(
            import_module("crewai.llm").LLM, "set_callbacks", None
        )
        wrap_function_wrapper(
            module="crewai.llm",
            name="LLM.set_callbacks",
            wrapper=_set_callbacks,
        )

    def _uninstrument(self, **kwargs: Any) -> None:
        if self._original_execute_core is not None:
            task_module = import_module("crewai")
            task_module.Task._execute_core = self._original_execute_core
            self._original_execute_core = None

        if self._original_kickoff is not None:
            crew_module = import_module("crewai")
            crew_module.Crew.kickoff = self._original_kickoff
            self._original_kickoff = None

        if self._original_tool_use is not None:
            tool_usage_module = import_module("crewai.tools.tool_usage")
            tool_usage_module.ToolUsage._use = self._original_tool_use
            self._original_tool_use = None

        if self._original_set_callbacks is not None:
            llm_module = import_module("crewai.llm")
            llm_module.LLM.set_callbacks = self._original_set_callbacks
            self._original_set_callbacks = None
