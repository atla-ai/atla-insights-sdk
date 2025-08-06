"""LangChain instrumentation."""

from typing import ContextManager

from atla_insights.main import ATLA_INSTANCE
from atla_insights.suppression import NoOpContextManager, is_instrumentation_suppressed


def instrument_langchain() -> ContextManager[None]:
    """Instrument the LangChain framework.

    This function creates a context manager that instruments the LangChain framework,
    within its context.

    This includes LangChain-derived frameworks such as e.g. LangGraph.

    See [LangChain docs](https://python.langchain.com/docs) for usage details on the
    framework itself.

    ```py
    from atla_insights import instrument_langchain

    with instrument_langchain():
        # My LangChain code here
    ```

    :return (ContextManager[None]): A context manager that instruments LangChain.
    """
    if is_instrumentation_suppressed():
        return NoOpContextManager()

    from atla_insights.frameworks.instrumentors.langchain import AtlaLangChainInstrumentor

    langchain_instrumentor = AtlaLangChainInstrumentor()

    return ATLA_INSTANCE.instrument_service(
        service=AtlaLangChainInstrumentor.name,
        instrumentors=[langchain_instrumentor],
    )


def uninstrument_langchain() -> None:
    """Uninstrument the LangChain framework."""
    if is_instrumentation_suppressed():
        return

    from atla_insights.frameworks.instrumentors.langchain import AtlaLangChainInstrumentor

    return ATLA_INSTANCE.uninstrument_service(AtlaLangChainInstrumentor.name)
