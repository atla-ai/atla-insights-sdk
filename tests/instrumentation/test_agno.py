"""Unit tests for the Agno instrumentation."""

import pytest
from agno.agent import Agent
from agno.models.litellm import LiteLLM
from agno.models.openai import OpenAIChat
from openai import OpenAI
from openinference.instrumentation.agno import AgnoInstrumentor

from tests._otel import BaseLocalOtel


@pytest.mark.usefixtures("mock_openai_client")
class TestAgnoInstrumentation(BaseLocalOtel):
    """Test the Agno instrumentation."""

    def test_basic_with_openai(self, mock_openai_client: OpenAI) -> None:
        """Test the Agno instrumentation with OpenAI."""
        from src.atla_insights import instrument_openai

        agent = Agent(
            model=OpenAIChat(
                id="mock-model",
                base_url=str(mock_openai_client.base_url),
                api_key="unit-test",
            ),
        )

        # NOTE: testing workaround because of a lack of OpenAI .uninstrument() support.
        AgnoInstrumentor().instrument()
        with instrument_openai():
            agent.print_response("Hello world!")

        finished_spans = self.get_finished_spans()

        assert len(finished_spans) == 3
        run, llm_call, request = finished_spans

        assert run.name == "Agent.run"
        assert llm_call.name == "OpenAIChat.invoke"
        assert request.name == "Chat Completion with {request_data[model]!r}"

        assert request.attributes is not None
        assert request.attributes.get("request_data")

    def test_basic_with_litellm(self, mock_openai_client: OpenAI) -> None:
        """Test the Agno instrumentation with LiteLLM."""
        from src.atla_insights import instrument_agno

        agent = Agent(
            model=LiteLLM(
                id="gpt-4o-mini",
                api_base=str(mock_openai_client.base_url),
                api_key="unit-test",
            ),
        )

        instrument_agno("litellm")

        agent.print_response("Hello world!")

        finished_spans = self.get_finished_spans()

        assert len(finished_spans) == 3
        run, llm_call, request = finished_spans

        assert run.name == "Agent.run"
        assert llm_call.name == "LiteLLM.invoke"
        assert request.name == "litellm_request"

        assert request.attributes is not None
        assert (
            request.attributes.get("llm.openai.messages")
            == "[{'role': 'user', 'content': 'Hello world!'}]"
        )
