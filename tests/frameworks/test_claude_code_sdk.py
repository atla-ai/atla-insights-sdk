"""Test the Claude Code SDK instrumentation."""

import asyncio

import pytest
from claude_code_sdk import ClaudeCodeOptions, query

from tests._otel import BaseLocalOtel


class TestClaudeCodeSdkInstrumentation(BaseLocalOtel):
    """Test the Claude Code SDK instrumentation."""

    @pytest.mark.asyncio
    async def test_basic(self) -> None:
        """Test basic Claude Code SDK instrumentation."""
        from atla_insights import instrument_claude_code_sdk

        with instrument_claude_code_sdk():
            async for _ in query(
                prompt="foo",
                options=ClaudeCodeOptions(
                    system_prompt="You are a helpful assistant.",
                    allowed_tools=["Bash", "Read", "WebSearch"],
                ),
            ):
                await asyncio.sleep(0.01)  # simulate activity
            await asyncio.sleep(0.01)  # simulate activity

        async for _ in query(
            prompt="foo",
            options=ClaudeCodeOptions(
                system_prompt="You are a helpful assistant.",
                allowed_tools=["Bash", "Read", "WebSearch"],
            ),
        ):
            await asyncio.sleep(0.01)  # simulate activity
        await asyncio.sleep(0.01)  # simulate activity

        finished_spans = self.get_finished_spans()

        assert len(finished_spans) == 1

        [llm_call] = finished_spans

        assert llm_call.name == "Claude Code SDK Response"

    def test_tool_result_in_input_is_marked_as_tool(self) -> None:
        """Ensure input messages with tool_result are labeled as role 'tool'."""
        from atla_insights.frameworks.instrumentors.claude_code_sdk import (
            _get_input_messages,
        )

        messages = [
            {
                "role": "user",
                "content": [
                    {"type": "tool_result", "content": "some tool output"},
                ],
            }
        ]

        attrs = dict(_get_input_messages(messages, options={}))

        assert attrs.get("llm.input_messages.0.message.role") == "tool"

    def test_tool_result_in_output_is_converted_to_tool_input(self) -> None:
        """Ensure prior tool_result message is recorded as tool role in inputs."""
        from atla_insights.frameworks.instrumentors.claude_code_sdk import (
            _get_output_messages,
        )

        messages = [
            {
                "type": "user",
                "message": {
                    "role": "user",
                    "content": [
                        {"type": "tool_result", "content": "tool response"},
                    ],
                },
            },
            {
                "type": "assistant",
                "message": {
                    "role": "assistant",
                    "content": [{"type": "text", "text": "assistant text"}],
                },
            },
        ]

        # num_inputs=1: first message is counted as the first input
        attrs = dict(_get_output_messages(messages, num_inputs=1))

        # assistant output preserved
        assert attrs.get("llm.output_messages.0.message.role") == "assistant"
        assert attrs.get("llm.output_messages.0.message.content") == "assistant text"

        # prior message with tool_result becomes an input with role 'tool'
        assert attrs.get("llm.input_messages.1.message.role") == "tool"
