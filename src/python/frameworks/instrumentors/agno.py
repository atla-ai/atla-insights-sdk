"""Agno instrumentation."""

from typing import Any

try:
    from openinference.instrumentation.agno import AgnoInstrumentor
except ImportError as e:
    raise ImportError(
        "Agno instrumentation needs to be installed. "
        'Please install it via `pip install "atla-insights[agno]"`.'
    ) from e


class AtlaAgnoInstrumentor(AgnoInstrumentor):
    """Atla Agno instrumentor class."""

    name = "agno"

    def _uninstrument(self, **kwargs: Any) -> None:
        # Custom uninstrumentation to ensure Agno framework remains fully functional
        # afterwards.
        from agno.agent import Agent
        from agno.team import Team
        from agno.tools.function import FunctionCall

        if self._original_run_method is not None:
            Agent._run = self._original_run_method  # type: ignore[method-assign]
            self._original_run_method = None

        if self._original_run_stream_method is not None:
            Agent._run_stream = self._original_run_stream_method  # type: ignore[method-assign]
            self._original_run_stream_method = None

        if self._original_arun_method is not None:
            Agent._arun = self._original_arun_method  # type: ignore[method-assign]
            self._original_arun_method = None

        if self._original_arun_stream_method is not None:
            Agent._arun_stream = self._original_arun_stream_method  # type: ignore[method-assign]
            self._original_arun_stream_method = None

        if self._original_team_run_method is not None:
            Team._run = self._original_team_run_method  # type: ignore[method-assign]
            self._original_team_run_method = None

        if self._original_team_run_stream_method is not None:
            Team._run_stream = self._original_team_run_stream_method  # type: ignore[method-assign]
            self._original_team_run_stream_method = None

        if self._original_team_arun_method is not None:
            Team._arun = self._original_team_arun_method  # type: ignore[method-assign]
            self._original_team_arun_method = None

        if self._original_team_arun_stream_method is not None:
            Team._arun_stream = self._original_team_arun_stream_method  # type: ignore[method-assign]
            self._original_team_arun_stream_method = None

        if self._original_model_call_methods is not None:
            for (
                model_subclass,
                original_model_call_methods,
            ) in self._original_model_call_methods.items():
                for method_name, method in original_model_call_methods.items():
                    setattr(model_subclass, method_name, method)
            self._original_model_call_methods = None

        if self._original_function_execute_method is not None:
            FunctionCall.execute = self._original_function_execute_method  # type: ignore[method-assign]
            self._original_function_execute_method = None

        if self._original_function_aexecute_method is not None:
            FunctionCall.aexecute = self._original_function_aexecute_method  # type: ignore[method-assign]
            self._original_function_aexecute_method = None
