"""Unit tests for the OpenAI Agents instrumentation."""

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
        from src.atla_insights import instrument_openai_agents

        instrument_openai_agents()

        set_default_openai_client(mock_async_openai_client, use_for_tracing=False)

        agent = Agent(name="Hello world", instructions="You are a helpful agent.")
        result = await Runner.run(agent, "Hello world")

        assert result.final_output == "hello world"

        finished_spans = self.get_finished_spans()

        assert len(finished_spans) == 3
        trace, run, request = finished_spans

        assert trace.name == "OpenAI Agents trace: {name}"
        assert run.name == "Agent run: {name!r}"
        assert request.name == "Responses API with {gen_ai.request.model!r}"

        assert request.attributes is not None
        assert "events" in request.attributes
