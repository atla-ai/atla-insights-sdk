"""Unit tests for the OpenAI Agents instrumentation."""

import pytest
from agents import Agent, OpenAIChatCompletionsModel, Runner, set_default_openai_client
from openai import AsyncOpenAI

from tests._otel import BaseLocalOtel


class TestOpenaiAgentsInstrumentation(BaseLocalOtel):
    """Test the OpenAI Agents instrumentation."""

    @pytest.mark.asyncio
    async def test_basic(self, mock_async_openai_client: AsyncOpenAI) -> None:
        """Test the OpenAI Agents integration."""
        from src.atla_insights import instrument_openai_agents

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
        from src.atla_insights import instrument_openai_agents

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
