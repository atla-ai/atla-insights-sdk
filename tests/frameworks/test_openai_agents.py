"""Unit tests for the OpenAI Agents instrumentation."""

from typing import Any, cast

import pytest
from agents import (
    Agent,
    OpenAIChatCompletionsModel,
    RunConfig,
    RunHooks,
    Runner,
    set_default_openai_client,
)
from agents._run_impl import RunImpl, ToolRunFunction, TraceCtxManager
from agents.run_context import RunContextWrapper
from agents.tool import function_tool
from openai import AsyncOpenAI
from openai.types.responses import ResponseFunctionToolCall

from tests._otel import BaseLocalOtel


class TestOpenaiAgentsInstrumentation(BaseLocalOtel):
    """Test the OpenAI Agents instrumentation."""

    @pytest.mark.asyncio
    async def test_basic(self, mock_async_openai_client: AsyncOpenAI) -> None:
        """Test the OpenAI Agents integration."""
        from atla_insights import instrument_openai_agents

        set_default_openai_client(mock_async_openai_client, use_for_tracing=False)

        with instrument_openai_agents():
            agent = Agent(name="Hello world", instructions="You are a helpful agent.")
            result = await Runner.run(agent, "Hello world")

        assert result.final_output == "hello world"

        finished_spans = self.get_finished_spans()

        assert len(finished_spans) == 4
        workflow, trace, run, request = finished_spans

        assert workflow.name == "Agent workflow"
        assert trace.name == "Hello world"
        assert run.name == "response"
        assert request.name == "Response"

        assert request.attributes is not None

        assert request.attributes.get("llm.input_messages.0.message.role") == "system"
        assert request.attributes.get("llm.input_messages.1.message.role") == "user"

        assert request.attributes.get("llm.output_messages.0.message.role") == "assistant"
        assert (
            request.attributes.get(
                "llm.output_messages.0.message.contents.0.message_content.type"
            )
            == "text"
        )
        assert (
            request.attributes.get(
                "llm.output_messages.0.message.contents.0.message_content.text"
            )
            == "hello world"
        )

    @pytest.mark.asyncio
    async def test_chat_completion(self, mock_async_openai_client: AsyncOpenAI) -> None:
        """Test the OpenAI Agents integration with chat completions."""
        from atla_insights import instrument_openai_agents

        with instrument_openai_agents():
            agent = Agent(
                name="Hello world",
                instructions="You are a helpful agent.",
                model=OpenAIChatCompletionsModel(
                    model="some-model",
                    openai_client=mock_async_openai_client,
                ),
            )
            result = await Runner.run(agent, "Hello world")

        assert result.final_output == "hello world"

        finished_spans = self.get_finished_spans()

        assert len(finished_spans) == 4
        workflow, trace, run, request = finished_spans

        assert workflow.name == "Agent workflow"
        assert trace.name == "Hello world"
        assert run.name == "generation"
        assert request.name == "ChatCompletion"

        assert request.attributes is not None

        assert request.attributes.get("llm.input_messages.0.message.role") == "system"
        assert request.attributes.get("llm.input_messages.1.message.role") == "user"

        assert request.attributes.get("llm.output_messages.0.message.role") == "assistant"
        assert (
            request.attributes.get("llm.output_messages.0.message.content")
            == "hello world"
        )

    @pytest.mark.asyncio
    async def test_tool_invocation(self, mock_async_openai_client: AsyncOpenAI) -> None:
        """Test the OpenAI Agents SDK instrumentation with tool invocation."""
        from atla_insights import instrument_openai_agents

        with instrument_openai_agents():
            with TraceCtxManager(
                workflow_name="unit-test",
                trace_id="abc-123",
                group_id="abc-123",
                metadata={"some": "metadata"},
                disabled=False,
            ):

                @function_tool
                def test_function(some_arg: str) -> str:
                    """Test function."""
                    return "some-result"

                await RunImpl.execute_function_tool_calls(
                    agent=Agent(
                        name="Hello world",
                        instructions="You are a helpful agent.",
                        model=OpenAIChatCompletionsModel(
                            model="some-model",
                            openai_client=mock_async_openai_client,
                        ),
                    ),
                    tool_runs=[
                        ToolRunFunction(
                            tool_call=ResponseFunctionToolCall(
                                arguments='{"some_arg": "some-value"}',
                                call_id="abc123",
                                type="function_call",
                                name="test_function",
                            ),
                            function_tool=test_function,
                        ),
                    ],
                    hooks=RunHooks(),
                    context_wrapper=cast(RunContextWrapper[Any], RunContextWrapper({})),
                    config=RunConfig(),
                )

        finished_spans = self.get_finished_spans()
        assert len(finished_spans) == 2

        root_span, tool_span = finished_spans

        assert root_span.name == "unit-test"
        assert tool_span.name == "test_function"

        assert tool_span.attributes is not None
        assert tool_span.attributes.get("openinference.span.kind") == "TOOL"

        assert tool_span.attributes.get("tool.name") == "test_function"
        # TODO: Add test for tool description once supported.
        assert tool_span.attributes.get("tool.parameters") == '{"some_arg": "some-value"}'

        assert tool_span.attributes.get("input.value") == '{"some_arg": "some-value"}'
        assert tool_span.attributes.get("output.value") == "some-result"
