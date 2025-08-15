"""Test the Claude Code SDK instrumentation."""

import asyncio

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
                    system_prompt="You are a helpful assistant.",
                    allowed_tools=["Bash", "Read", "WebSearch"],
                )
            ) as client:
                await client.query("Hello world!")

                async for _ in client.receive_response():
                    await asyncio.sleep(0.01)  # simulate activity
                await asyncio.sleep(0.01)  # simulate activity

        # Run again to make sure uninstrumentation works
        async with ClaudeSDKClient(
            options=ClaudeCodeOptions(
                system_prompt="You are a helpful assistant",
                allowed_tools=["Bash", "Read", "WebSearch"],
            )
        ) as client:
            await client.query("Hello world once again!")

            async for _ in client.receive_response():
                await asyncio.sleep(0.01)  # simulate activity
            await asyncio.sleep(0.01)  # simulate activity

        finished_spans = self.get_finished_spans()

        assert len(finished_spans) == 1

        [llm_call] = finished_spans

        assert llm_call.name == "Claude Code SDK Response"

        assert llm_call.attributes is not None
        assert llm_call.attributes.get("llm.input_messages.0.message.role") == "system"
        assert (
            llm_call.attributes.get("llm.input_messages.0.message.content")
            == "You are a helpful assistant."
        )
        assert llm_call.attributes.get("llm.input_messages.1.message.role") == "user"
        assert llm_call.attributes.get("llm.input_messages.1.message.content") == "foo"
        assert (
            llm_call.attributes.get("llm.output_messages.0.message.role") == "assistant"
        )
        assert llm_call.attributes.get("llm.output_messages.0.message.content") == "bar"
