"""Unit tests for the Agno integration."""

import litellm
import logfire
import pytest
from agno.agent import Agent
from agno.models.litellm import LiteLLM
from agno.models.openai import OpenAIChat
from openai import OpenAI
from opentelemetry.sdk.trace.export import SimpleSpanProcessor
from opentelemetry.sdk.trace.export.in_memory_span_exporter import InMemorySpanExporter

from src.atla_insights import instrument_agno, instrument_litellm, instrument_openai


@pytest.mark.usefixtures("mock_openai_client")
class TestAgnoIntegration:
    """Test the Agno integration."""

    in_memory_span_exporter: InMemorySpanExporter

    @classmethod
    def setup_class(cls) -> None:
        """Set up an in-memory span exporter to collect traces to a local object."""
        cls.in_memory_span_exporter = InMemorySpanExporter()

        logfire.configure(
            additional_span_processors=[SimpleSpanProcessor(cls.in_memory_span_exporter)],
            send_to_logfire=False,
        )

        instrument_agno()

    def setup_method(self) -> None:
        """Wipe any pre-existing litellm instrumentation."""
        litellm.callbacks = []
        instrument_litellm()

    def teardown_method(self) -> None:
        """Wipe any added traces after each test run."""
        self.in_memory_span_exporter.clear()

    def test_openai(self, mock_openai_client: OpenAI) -> None:
        """Test the Agno integration with OpenAI."""
        agent = Agent(
            model=OpenAIChat(
                id="mock-model",
                base_url=str(mock_openai_client.base_url),
                api_key="unit-test",
            ),
        )

        with instrument_openai():
            agent.print_response("Hello world!")

        assert len(self.in_memory_span_exporter.get_finished_spans()) == 3

        request, llm_call, run = self.in_memory_span_exporter.get_finished_spans()

        assert request.name == "Chat Completion with {request_data[model]!r}"
        assert llm_call.name == "OpenAIChat.invoke"
        assert run.name == "Agent.run"

        assert request.attributes is not None
        assert request.attributes.get("request_data")

    def test_litellm(self, mock_openai_client: OpenAI) -> None:
        """Test the Agno integration with LiteLLM."""
        agent = Agent(
            model=LiteLLM(
                id="gpt-4o-mini",
                api_base=str(mock_openai_client.base_url),
                api_key="unit-test",
            ),
        )

        instrument_litellm()

        agent.print_response("Hello world!")

        assert len(self.in_memory_span_exporter.get_finished_spans()) == 3

        llm_call, request, run = self.in_memory_span_exporter.get_finished_spans()

        assert request.name == "litellm_request"
        assert llm_call.name == "LiteLLM.invoke"
        assert run.name == "Agent.run"

        assert request.attributes is not None
        assert (
            request.attributes.get("llm.openai.messages")
            == "[{'role': 'user', 'content': 'Hello world!'}]"
        )
