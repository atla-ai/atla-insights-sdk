"""Utility functions for framework instrumentation."""

from opentelemetry.instrumentation.instrumentor import (  # type: ignore[attr-defined]
    BaseInstrumentor,
)

from atla_insights.constants import LLM_PROVIDER_TYPE
from atla_insights.main import ATLA_INSTANCE


def get_instrumentors_for_provider(
    llm_provider: LLM_PROVIDER_TYPE,
) -> list[BaseInstrumentor]:
    """Get the instrumentor(s) for given LLM provider(s).

    Returns a list of instantiated OpenTelemetry instrumentors for given LLM provider(s).

    :param llm_provider (LLM_PROVIDER_TYPE): The LLM provider(s) to instrument.
    :return (list[BaseInstrumentor]): The instrumentor(s) for the given LLM provider(s).
    """
    if isinstance(llm_provider, str):
        llm_provider = [llm_provider]

    instrumentors: list[BaseInstrumentor] = []
    for provider in llm_provider:
        match provider:
            case "anthropic":
                try:
                    from openinference.instrumentation.anthropic import (
                        AnthropicInstrumentor,
                    )
                except ImportError as e:
                    raise ImportError(
                        "Anthropic instrumentation needs to be installed. "
                        'Please install it via `pip install "atla-insights[anthropic]"`.'
                    ) from e

                instrumentors.append(AnthropicInstrumentor())
            case "google-genai":
                from atla_insights.llm_providers.instrumentors.google_genai import (
                    AtlaGoogleGenAIInstrumentor,
                )

                instrumentors.append(AtlaGoogleGenAIInstrumentor())
            case "litellm":
                from atla_insights.llm_providers.instrumentors.litellm import (
                    AtlaLiteLLMIntrumentor,
                )

                instrumentors.append(
                    AtlaLiteLLMIntrumentor(tracer=ATLA_INSTANCE.get_tracer())
                )
            case "openai":
                try:
                    from openinference.instrumentation.openai import OpenAIInstrumentor
                except ImportError as e:
                    raise ImportError(
                        "OpenAI instrumentation needs to be installed. "
                        'Please install it via `pip install "atla-insights[openai]"`.'
                    ) from e

                instrumentors.append(OpenAIInstrumentor())
            case _:
                raise ValueError(f"Invalid LLM provider: {provider}")

    return instrumentors
