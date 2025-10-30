"""Claude Agent SDK instrumentation."""

from typing import ContextManager, cast

from opentelemetry.sdk.trace import TracerProvider

from atla_insights.main import ATLA_INSTANCE
from atla_insights.suppression import NoOpContextManager, is_instrumentation_suppressed


def instrument_claude_agent_sdk() -> ContextManager[None]:
    """Instrument the Claude Agent SDK.

    This function creates a context manager that instruments the Claude Agent SDK,
    within its context.

    ```py
    from atla_insights import instrument_claude_agent_sdk

    with instrument_claude_agent_sdk():
        # My Claude Agent SDK usage here
    ```

    :return (ContextManager[None]): A context manager that instruments Claude Agent SDK.
    """
    if is_instrumentation_suppressed():
        return NoOpContextManager()

    from atla_insights.frameworks.instrumentors.claude_agent_sdk import (
        AtlaClaudeAgentSdkInstrumentor,
    )

    tracer = cast(TracerProvider, ATLA_INSTANCE.tracer_provider).get_tracer(
        "openinference.instrumentation.claude_agent_sdk"
    )
    claude_agent_sdk_instrumentor = AtlaClaudeAgentSdkInstrumentor(tracer=tracer)

    return ATLA_INSTANCE.instrument_service(
        service=AtlaClaudeAgentSdkInstrumentor.name,
        instrumentors=[claude_agent_sdk_instrumentor],
    )


def uninstrument_claude_agent_sdk() -> None:
    """Uninstrument the Claude Agent SDK."""
    if is_instrumentation_suppressed():
        return

    from atla_insights.frameworks.instrumentors.claude_agent_sdk import (
        AtlaClaudeAgentSdkInstrumentor,
    )

    return ATLA_INSTANCE.uninstrument_service(AtlaClaudeAgentSdkInstrumentor.name)
