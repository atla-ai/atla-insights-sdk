"""OpenAI Agents SDK instrumentation."""

from typing import ContextManager

from atla_insights.constants import LLM_PROVIDER_TYPE
from atla_insights.frameworks.utils import get_instrumentors_for_provider
from atla_insights.main import ATLA_INSTANCE


def instrument_openai_agents(
    llm_provider: LLM_PROVIDER_TYPE = "openai",
) -> ContextManager[None]:
    """Instrument the OpenAI Agents SDK.

    This function creates a context manager that instruments the OpenAI Agents SDK, within
    its context.

    See [OpenAI Agents SDK docs](https://openai.github.io/openai-agents-python/) for usage
    details on the SDK itself.

    ```py
    from atla_insights import instrument_openai_agents

    with instrument_openai_agents():
        # My OpenAI Agents SDK code here
    ```

    :param llm_provider (LLM_PROVIDER_TYPE): The LLM provider(s) to instrument. Defaults
        to "openai".
    :return (ContextManager[None]): A context manager that instruments OpenAI Agents SDK.
    """
    from atla_insights.frameworks.instrumentors.openai_agents import (
        AtlaOpenAIAgentsInstrumentor,
    )

    # Create an instrumentor for the OpenAI Agents SDK.
    openai_agents_instrumentor = AtlaOpenAIAgentsInstrumentor()

    # Create an instrumentor for the underlying LLM provider(s).
    llm_provider_instrumentors = get_instrumentors_for_provider(llm_provider)

    return ATLA_INSTANCE.instrument_service(
        service=AtlaOpenAIAgentsInstrumentor.name,
        instrumentors=[openai_agents_instrumentor, *llm_provider_instrumentors],
    )


def uninstrument_openai_agents() -> None:
    """Uninstrument the OpenAI Agents SDK."""
    from atla_insights.frameworks.instrumentors.openai_agents import (
        AtlaOpenAIAgentsInstrumentor,
    )

    return ATLA_INSTANCE.uninstrument_service(AtlaOpenAIAgentsInstrumentor.name)
