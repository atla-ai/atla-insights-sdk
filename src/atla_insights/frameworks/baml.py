"""BAML instrumentation logic."""

from typing import ContextManager, Literal, Optional

from atla_insights.constants import SUPPORTED_LLM_FORMAT
from atla_insights.main import ATLA_INSTANCE
from atla_insights.suppression import NoOpContextManager, is_instrumentation_suppressed


def instrument_baml(
    llm_provider: SUPPORTED_LLM_FORMAT,
    *,
    include_functions: list[str] | Literal["all"] = "all",
    exclude_functions: Optional[list[str]] = None,
) -> ContextManager[None]:
    """Instrument the BAML framework.

    This function creates a context manager that instruments the BAML framework, within
    its context, and for certain provided LLM provider(s).

    See [BAML docs](https://docs.boundaryml.com/) for usage details on the framework
    itself.

    ```py
    from atla_insights import instrument_baml

    # The LLM provider I am using within BAML (e.g. `provider anthropic`)
    my_llm_provider = "anthropic"

    with instrument_baml(my_llm_provider):
        # My BAML code here
    ```

    :param llm_provider (SUPPORTED_LLM_PROVIDER): The LLM provider to instrument.
    :param include_functions (list[str] | "all"): A list of BAML function names to
        instrument. All other BAML functions will not be instrumented.
        Defaults to "all" (every BAML function will be instrumented).
    :param exclude_functions (list[str] | None): A list of BAML function names to
        exclude from instrumentation. All other BAML functions will be instrumented.
        Defaults to None (every BAML function will be instrumented).
    :return (ContextManager[None]): A context manager that instruments BAML.
    """
    if is_instrumentation_suppressed():
        return NoOpContextManager()

    if include_functions != "all" and exclude_functions is not None:
        raise ValueError(
            "Cannot provide both include_functions and exclude_functions. "
            "Please provide only one of these parameters."
        )

    from atla_insights.frameworks.instrumentors.baml import AtlaBamlInstrumentor

    # Create an instrumentor for the BAML framework.
    baml_instrumentor = AtlaBamlInstrumentor(
        llm_provider=llm_provider,
        include_functions=include_functions,
        exclude_functions=exclude_functions,
    )

    return ATLA_INSTANCE.instrument_service(
        service=AtlaBamlInstrumentor.name,
        instrumentors=[baml_instrumentor],
    )


def uninstrument_baml() -> None:
    """Uninstrument the BAML framework."""
    if is_instrumentation_suppressed():
        return

    from atla_insights.frameworks.instrumentors.baml import AtlaBamlInstrumentor

    return ATLA_INSTANCE.uninstrument_service(AtlaBamlInstrumentor.name)
