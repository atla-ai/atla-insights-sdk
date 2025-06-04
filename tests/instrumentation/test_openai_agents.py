"""Unit tests for the OpenAI Agents instrumentation."""

import time

import pytest
from agents import Agent, Runner, set_default_openai_client
from openai import AsyncOpenAI

from tests._otel import BaseLocalOtel


@pytest.mark.usefixtures("mock_async_openai_client")
class TestOpenaiAgentsInstrumentation(BaseLocalOtel):
    """Test the OpenAI Agents instrumentation."""

    @pytest.mark.asyncio
    async def test_basic(self, mock_async_openai_client: AsyncOpenAI) -> None:
        """Test the OpenAI Agents integration."""
        from openinference.instrumentation.openai import OpenAIInstrumentor
        from openinference.instrumentation.openai_agents import OpenAIAgentsInstrumentor

        set_default_openai_client(mock_async_openai_client, use_for_tracing=False)

        OpenAIAgentsInstrumentor().instrument()
        openai_instrumentor = OpenAIInstrumentor()
        openai_instrumentor.instrument()

        agent = Agent(name="Hello world", instructions="You are a helpful agent.")
        result = await Runner.run(agent, "Hello world")
        openai_instrumentor._uninstrument()

        assert result.final_output == "hello world"

        time.sleep(1)  # wait for the spans to be finished

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
