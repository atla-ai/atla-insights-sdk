"""Agno instrumentation logic."""

from typing import ContextManager

from atla_insights.constants import LLM_PROVIDER_TYPE
from atla_insights.frameworks.utils import get_instrumentors_for_provider
from atla_insights.main import ATLA_INSTANCE


def instrument_agno(llm_provider: LLM_PROVIDER_TYPE) -> ContextManager[None]:
    """Instrument the Agno framework.

    This function creates a context manager that instruments the Agno framework, within
    its context, and for certain provided LLM provider(s).

    See [Agno docs](https://docs.agno.com/) for usage details on the framework itself.

    ```py
    from atla_insights import instrument_agno

    # The LLM provider I am using within Agno (e.g. as an `OpenAIChat` object)
    my_llm_provider = "openai"

    with instrument_agno(my_llm_provider):
        # My Agno code here
    ```

    :param llm_provider (LLM_PROVIDER_TYPE): The LLM provider(s) to instrument.
    :return (ContextManager[None]): A context manager that instruments Agno.
    """
    from atla_insights.frameworks.instrumentors.agno import AtlaAgnoInstrumentor

    # Create an instrumentor for the Agno framework.
    agno_instrumentor = AtlaAgnoInstrumentor()

    # Create an instrumentor for the underlying LLM provider(s).
    llm_provider_instrumentors = get_instrumentors_for_provider(llm_provider)

    return ATLA_INSTANCE.instrument_service(
        service=AtlaAgnoInstrumentor.name,
        instrumentors=[*llm_provider_instrumentors, agno_instrumentor],
    )


def uninstrument_agno() -> None:
    """Uninstrument the Agno framework."""
    from atla_insights.frameworks.instrumentors.agno import AtlaAgnoInstrumentor

    return ATLA_INSTANCE.uninstrument_service(AtlaAgnoInstrumentor.name)
