"""OpenAI agents instrumentation."""

from typing import Any

try:
    from agents import set_trace_processors
    from openinference.instrumentation.openai_agents import OpenAIAgentsInstrumentor
except ImportError as e:
    raise ImportError(
        "OpenAI agents instrumentation needs to be installed. "
        "Please install it via `pip install atla-insights[openai-agents]`."
    ) from e


class AtlaOpenAIAgentsInstrumentor(OpenAIAgentsInstrumentor):
    """Atla OpenAI Agents SDK instrumentor class."""

    def _uninstrument(self, **kwargs: Any) -> None:
        set_trace_processors([])
