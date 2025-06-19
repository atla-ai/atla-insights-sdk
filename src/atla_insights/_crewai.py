"""CrewAI instrumentation."""

import os
from importlib import import_module
from typing import Any, Callable, Mapping, Tuple

from opentelemetry.trace import Tracer
from wrapt import wrap_function_wrapper

try:
    import litellm
    from crewai.telemetry.telemetry import Telemetry
    from crewai.utilities.events.event_listener import event_listener
    from openinference.instrumentation.crewai import CrewAIInstrumentor
    from openinference.instrumentation.crewai._wrappers import (
        _ExecuteCoreWrapper,
        _KickoffWrapper,
        _ToolUseWrapper,
    )
except ImportError as e:
    raise ImportError(
        "CrewAI instrumentation needs to be installed. "
        "Please install it via `pip install atla-insights[crewai]`."
    ) from e


def _set_callbacks(
    wrapped: Callable[..., Any],
    instance: Any,
    args: Tuple[Any, ...],
    kwargs: Mapping[str, Any],
) -> None:
    if callbacks := kwargs.get("callbacks"):
        for callback in callbacks:
            if callback not in litellm.callbacks:
                litellm.callbacks.append(callback)


class AtlaCrewAIInstrumentor(CrewAIInstrumentor):
    """Atla CrewAI instrumentator class."""

    def __init__(self, tracer: Tracer) -> None:
        super().__init__()
        self.tracer = tracer
        self.disable_crewai_telemetry()

    def disable_crewai_telemetry(self) -> None:
        """Disable the built-in CrewAI telemetry to avoid interfering with Atla."""
        os.environ["CREWAI_DISABLE_TELEMETRY"] = "true"
        event_listener._telemetry = Telemetry()

    def _instrument(self, **kwargs: Any) -> None:
        from crewai.llm import LLM

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

        self._original_set_callbacks = getattr(LLM, "set_callbacks", None)
        wrap_function_wrapper(
            module="crewai.llm",
            name="LLM.set_callbacks",
            wrapper=_set_callbacks,
        )

    def _uninstrument(self, **kwargs: Any) -> None:
        from crewai.llm import LLM

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
            LLM.set_callbacks = self._original_set_callbacks  # type: ignore[method-assign]
            self._original_set_callbacks = None
