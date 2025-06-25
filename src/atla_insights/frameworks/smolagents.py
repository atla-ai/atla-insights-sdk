"""HuggingFace SmolAgents instrumentation."""

from typing import ContextManager

from atla_insights.constants import LLM_PROVIDER_TYPE
from atla_insights.frameworks.utils import get_instrumentors_for_provider
from atla_insights.main import ATLA_INSTANCE


def instrument_smolagents(llm_provider: LLM_PROVIDER_TYPE) -> ContextManager[None]:
    """Instrument the HuggingFace SmolAgents framework.

    This function creates a context manager that instruments the SmolAgents framework,
    within its context.

    See [SmolAgents docs](https://huggingface.co/docs/smolagents) for usage details on
    the framework itself.

    ```py
    from atla_insights import instrument_smolagents

    # The LLM provider I am using within SmolAgents (e.g. as an `LiteLLMModel` object)
    my_llm_provider = "litellm"

    with instrument_smolagents(my_llm_provider):
        # My SmolAgents code here
    ```

    :param llm_provider (LLM_PROVIDER_TYPE): The LLM provider(s) to instrument.
    :return (ContextManager[None]): A context manager that instruments SmolAgents.
    """
    from atla_insights.frameworks.instrumentors.smolagents import (
        AtlaSmolAgentsInstrumentor,
    )

    # Create an instrumentor for the SmolAgents framework.
    smolagents_instrumentor = AtlaSmolAgentsInstrumentor()

    # Create an instrumentor for the underlying LLM provider(s).
    llm_provider_instrumentors = get_instrumentors_for_provider(llm_provider)

    return ATLA_INSTANCE.instrument_service(
        service=AtlaSmolAgentsInstrumentor.name,
        instrumentors=[smolagents_instrumentor, *llm_provider_instrumentors],
    )


def uninstrument_smolagents() -> None:
    """Uninstrument the HuggingFace SmolAgents framework."""
    from atla_insights.frameworks.instrumentors.smolagents import (
        AtlaSmolAgentsInstrumentor,
    )

    return ATLA_INSTANCE.uninstrument_service(AtlaSmolAgentsInstrumentor.name)
