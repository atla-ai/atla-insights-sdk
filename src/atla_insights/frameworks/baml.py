"""BAML instrumentation logic."""

from typing import ContextManager

from atla_insights.constants import LLM_PROVIDER_TYPE
from atla_insights.frameworks.utils import get_instrumentors_for_provider
from atla_insights.main import ATLA_INSTANCE


def instrument_baml(llm_provider: LLM_PROVIDER_TYPE) -> ContextManager[None]:
    """Instrument the BAML framework.

    This function creates a context manager that instruments the BAML framework, within
    its context, and for certain provided LLM provider(s).

    See [BAML docs](https://docs.boundaryml.com/) for usage details on the framework
    itself.

    ```py
    from atla_insights import instrument_baml

    # The LLM provider I am using within BAML (e.g. as an `OpenAIChat` object)
    my_llm_provider = "openai"

    with instrument_baml(my_llm_provider):
        # My BAML code here
    ```

    :param llm_provider (LLM_PROVIDER_TYPE): The LLM provider(s) to instrument.
    :return (ContextManager[None]): A context manager that instruments BAML.
    """
    from atla_insights.frameworks.instrumentors.baml import AtlaBamlInstrumentor

    # Create an instrumentor for the BAML framework.
    baml_instrumentor = AtlaBamlInstrumentor()

    # Create an instrumentor for the underlying LLM provider(s).
    llm_provider_instrumentors = get_instrumentors_for_provider(llm_provider)

    return ATLA_INSTANCE.instrument_service(
        service=AtlaBamlInstrumentor.name,
        instrumentors=[*llm_provider_instrumentors, baml_instrumentor],
    )


def uninstrument_baml() -> None:
    """Uninstrument the BAML framework."""
    from atla_insights.frameworks.instrumentors.baml import AtlaBamlInstrumentor

    return ATLA_INSTANCE.uninstrument_service(AtlaBamlInstrumentor.name)
