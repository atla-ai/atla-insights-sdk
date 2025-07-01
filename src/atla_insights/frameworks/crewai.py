"""CrewAI instrumentation."""

from typing import ContextManager

from atla_insights.frameworks.utils import get_instrumentors_for_provider
from atla_insights.main import ATLA_INSTANCE


def instrument_crewai() -> ContextManager[None]:
    """Instrument the CrewAI framework.

    This function creates a context manager that instruments the CrewAI framework, within
    its context.

    See [CrewAI docs](https://docs.crewai.com/) for usage details on the framework itself.

    ```py
    from atla_insights import instrument_crewai

    with instrument_crewai():
        # My CrewAI code here
    ```

    :return (ContextManager[None]): A context manager that instruments CrewAI.
    """
    from atla_insights.frameworks.instrumentors.crewai import AtlaCrewAIInstrumentor

    # Create an instrumentor for the CrewAI framework.
    crewai_instrumentor = AtlaCrewAIInstrumentor(ATLA_INSTANCE.get_tracer())

    # Create an instrumentor for the underlying LLM provider (always litellm).
    [llm_provider_instrumentor] = get_instrumentors_for_provider("litellm")

    return ATLA_INSTANCE.instrument_service(
        service=AtlaCrewAIInstrumentor.name,
        instrumentors=[crewai_instrumentor, llm_provider_instrumentor],
    )


def uninstrument_crewai() -> None:
    """Uninstrument the CrewAI framework."""
    from atla_insights.frameworks.instrumentors.crewai import AtlaCrewAIInstrumentor

    return ATLA_INSTANCE.uninstrument_service(AtlaCrewAIInstrumentor.name)
