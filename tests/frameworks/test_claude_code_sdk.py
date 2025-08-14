"""Test the Claude Code SDK instrumentation."""

import pytest
from claude_code_sdk import ClaudeCodeOptions, ClaudeSDKClient

from tests._otel import BaseLocalOtel


class TestClaudeCodeSdkInstrumentation(BaseLocalOtel):
    """Test the Claude Code SDK instrumentation."""

    @pytest.mark.asyncio
    async def test_basic(self) -> None:
        """Test basic Claude Code SDK instrumentation."""
        from atla_insights import instrument_claude_code_sdk

        with instrument_claude_code_sdk():
            async with ClaudeSDKClient(
                options=ClaudeCodeOptions(
                    system_prompt="You are a performance engineer",
                    allowed_tools=["Bash", "Read", "WebSearch"],
                )
            ) as client:
                await client.query("Hello world!")

                async for _ in client.receive_response():
                    ...

        # Run again to make sure uninstrumentation works
        async with ClaudeSDKClient(
            options=ClaudeCodeOptions(
                system_prompt="You are a performance engineer",
                allowed_tools=["Bash", "Read", "WebSearch"],
            )
        ) as client:
            await client.query("Hello world once again!")

            async for _ in client.receive_response():
                ...

        finished_spans = self.get_finished_spans()

        assert len(finished_spans) == 1

        [llm_call] = finished_spans

        assert llm_call.name == "Claude Code SDK Response"

        assert llm_call.attributes is not None
        assert llm_call.attributes.get("llm.input_messages.0.message.role") == "user"
        assert (
            llm_call.attributes.get("llm.input_messages.0.message.content")
            == "Hello world!"
        )
        assert (
            llm_call.attributes.get("llm.output_messages.0.message.role") == "assistant"
        )
        assert llm_call.attributes.get("llm.output_messages.0.message.content") == "hi"
