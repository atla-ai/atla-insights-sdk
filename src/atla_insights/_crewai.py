"""CrewAI instrumentation."""

from importlib import import_module
from typing import Any

from opentelemetry.trace import Tracer
from wrapt import wrap_function_wrapper

try:
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


class AtlaCrewAIInstrumentor(CrewAIInstrumentor):
    """Atla CrewAI instrumentator class."""

    def __init__(self, tracer: Tracer) -> None:
        super().__init__()
        self._tracer = tracer

    def _instrument(self, **kwargs: Any) -> None:
        execute_core_wrapper = _ExecuteCoreWrapper(tracer=self._tracer)
        self._original_execute_core = getattr(
            import_module("crewai").Task, "_execute_core", None
        )
        wrap_function_wrapper(
            module="crewai",
            name="Task._execute_core",
            wrapper=execute_core_wrapper,
        )

        kickoff_wrapper = _KickoffWrapper(tracer=self._tracer)
        self._original_kickoff = getattr(import_module("crewai").Crew, "kickoff", None)
        wrap_function_wrapper(
            module="crewai",
            name="Crew.kickoff",
            wrapper=kickoff_wrapper,
        )

        use_wrapper = _ToolUseWrapper(tracer=self._tracer)
        self._original_tool_use = getattr(
            import_module("crewai.tools.tool_usage").ToolUsage, "_use", None
        )
        wrap_function_wrapper(
            module="crewai.tools.tool_usage",
            name="ToolUsage._use",
            wrapper=use_wrapper,
        )
