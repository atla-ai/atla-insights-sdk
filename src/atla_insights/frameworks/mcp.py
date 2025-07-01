"""MCP instrumentation."""

from typing import ContextManager

from atla_insights.main import ATLA_INSTANCE


def instrument_mcp() -> ContextManager[None]:
    """Instrument the MCP (Model Context Protocol) calls.

    This function creates a context manager that instruments the MCP calls made by other
    (separately) instrumented frameworks and/or LLM providers.

    Note that this function only propagates the instrumented context to MCP calls and does
    **not** also instrument any framework or LLM provider.

    See [MCP docs](https://modelcontextprotocol.io/) for usage details on MCP itself.

    ```py
    from atla_insights import instrument_anthropic, instrument_mcp

    with instrument_mcp():
        with instrument_anthropic():
            # My Anthropic code here -> any MCP calls Anthropic will also be instrumented.
            # Note that this also works with other frameworks / providers than Anthropic.
    ```

    :return (ContextManager[None]): A context manager that instruments MCP calls.
    """
    try:
        from openinference.instrumentation.mcp import MCPInstrumentor
    except ImportError as e:
        raise ImportError(
            "MCP instrumentation needs to be installed. "
            'Please install it via `pip install "atla-insights[mcp]"`.'
        ) from e

    return ATLA_INSTANCE.instrument_service(
        service="mcp",
        instrumentors=[MCPInstrumentor()],
    )


def uninstrument_mcp() -> None:
    """Uninstrument MCP calls."""
    return ATLA_INSTANCE.uninstrument_service("mcp")
