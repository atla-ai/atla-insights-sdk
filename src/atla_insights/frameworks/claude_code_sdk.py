"""Claude Code SDK instrumentation."""

from typing import ContextManager, cast

from opentelemetry.sdk.trace import TracerProvider

from atla_insights.main import ATLA_INSTANCE
from atla_insights.suppression import NoOpContextManager, is_instrumentation_suppressed


def instrument_claude_code_sdk() -> ContextManager[None]:
    """Instrument the Claude Code SDK.

    Note that the `claude-code-sdk` package has been deprecated in favor of
    `claude-agent-sdk`. Please visit [the official migration guide](https://docs.claude.com/en/docs/claude-code/sdk/migration-guide)
    for information on how to migrate from Claude Code SDK to Claude Agent SDK.

    This instrumentation is only provided for backwards compatibility, and is **not** the
    intended way to instrument Claude Code.

    Please use `instrument_claude_agent_sdk` instead.

    This function creates a context manager that instruments the Claude Code SDK,
    within its context.

    ```py
    from atla_insights import instrument_claude_code_sdk

    with instrument_claude_code_sdk():
        # My Claude Code SDK usage here
    ```

    :return (ContextManager[None]): A context manager that instruments Claude Code SDK.
    """
    if is_instrumentation_suppressed():
        return NoOpContextManager()

    from atla_insights.frameworks.instrumentors.claude_code_sdk import (
        AtlaClaudeCodeSdkInstrumentor,
    )

    tracer = cast(TracerProvider, ATLA_INSTANCE.tracer_provider).get_tracer(
        "openinference.instrumentation.claude_code_sdk"
    )
    claude_code_sdk_instrumentor = AtlaClaudeCodeSdkInstrumentor(tracer=tracer)

    return ATLA_INSTANCE.instrument_service(
        service=AtlaClaudeCodeSdkInstrumentor.name,
        instrumentors=[claude_code_sdk_instrumentor],
    )


def uninstrument_claude_code_sdk() -> None:
    """Uninstrument the Claude Code SDK."""
    if is_instrumentation_suppressed():
        return

    from atla_insights.frameworks.instrumentors.claude_code_sdk import (
        AtlaClaudeCodeSdkInstrumentor,
    )

    return ATLA_INSTANCE.uninstrument_service(AtlaClaudeCodeSdkInstrumentor.name)
