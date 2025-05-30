"""Unit tests for the Agno integration."""

import logfire
import pytest
from agents import Agent, Runner, set_default_openai_client
from openai import AsyncOpenAI
from opentelemetry.sdk.trace.export import SimpleSpanProcessor
from opentelemetry.sdk.trace.export.in_memory_span_exporter import InMemorySpanExporter

from src.atla_insights import instrument_openai_agents


@pytest.mark.usefixtures("mock_async_openai_client")
class TestOpenaiAgentsIntegration:
    """Test the OpenAI Agents integration."""

    in_memory_span_exporter: InMemorySpanExporter

    @classmethod
    def setup_class(cls) -> None:
        """Set up an in-memory span exporter to collect traces to a local object."""
        cls.in_memory_span_exporter = InMemorySpanExporter()

        logfire.configure(
            additional_span_processors=[SimpleSpanProcessor(cls.in_memory_span_exporter)],
            send_to_logfire=False,
        )

        instrument_openai_agents()

    def teardown_method(self) -> None:
        """Wipe any added traces after each test run."""
        self.in_memory_span_exporter.clear()

    @pytest.mark.asyncio
    async def test_openai_agents(self, mock_async_openai_client: AsyncOpenAI) -> None:
        """Test the OpenAI Agents integration."""
        set_default_openai_client(mock_async_openai_client, use_for_tracing=False)

        agent = Agent(name="Hello world", instructions="You are a helpful agent.")
        result = await Runner.run(agent, "Hello world")

        assert result.final_output == "hello world"

        assert len(self.in_memory_span_exporter.get_finished_spans()) == 3

        trace, run, request = sorted(
            self.in_memory_span_exporter.get_finished_spans(),
            key=lambda x: x.start_time if x.start_time is not None else 0,
        )

        assert trace.name == "OpenAI Agents trace: {name}"
        assert run.name == "Agent run: {name!r}"
        assert request.name == "Responses API with {gen_ai.request.model!r}"

        assert request.attributes is not None
        assert "events" in request.attributes
