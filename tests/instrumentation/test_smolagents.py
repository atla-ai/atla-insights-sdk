"""Unit tests for the SmolAgents instrumentation."""

import pytest
from openai import OpenAI
from openinference.instrumentation.smolagents import SmolagentsInstrumentor
from smolagents import CodeAgent, LiteLLMModel, OpenAIServerModel

from tests._otel import BaseLocalOtel


@pytest.mark.usefixtures("mock_openai_client")
class TestSmolAgentsInstrumentation(BaseLocalOtel):
    """Test the SmolAgents instrumentation."""

    def test_basic_with_openai(self, mock_openai_client: OpenAI) -> None:
        """Test the SmolAgents instrumentation with OpenAI."""
        from src.atla_insights import instrument_openai

        agent = CodeAgent(
            model=OpenAIServerModel(
                model_id="mock-model",
                api_base=str(mock_openai_client.base_url),
                api_key="unit-test",
            ),
            tools=[],
        )

        # NOTE: testing workaround because of a lack of OpenAI .uninstrument() support.
        SmolagentsInstrumentor().instrument()
        with instrument_openai():
            agent.run("Hello world!", max_steps=1)

        finished_spans = self.get_finished_spans()

        assert len(finished_spans) == 3
        run, llm_call_1, llm_call_2 = finished_spans

        assert run.name == "CodeAgent.run"
        assert llm_call_1.name == "Chat Completion with {request_data[model]!r}"
        assert llm_call_2.name == "Chat Completion with {request_data[model]!r}"

        assert llm_call_1.attributes is not None
        assert llm_call_1.attributes.get("request_data")

        assert llm_call_2.attributes is not None
        assert llm_call_2.attributes.get("request_data")

    def test_basic_with_litellm(self, mock_openai_client: OpenAI) -> None:
        """Test the SmolAgents instrumentation with LiteLLM."""
        from src.atla_insights import instrument_smolagents

        agent = CodeAgent(
            model=LiteLLMModel(
                model_id="openai/mock-model",
                api_base=str(mock_openai_client.base_url),
                api_key="unit-test",
            ),
            tools=[],
        )

        instrument_smolagents("litellm")

        agent.run("Hello world!", max_steps=1)

        finished_spans = self.get_finished_spans()

        assert len(finished_spans) == 3
        run, llm_call_1, llm_call_2 = finished_spans

        assert run.name == "CodeAgent.run"
        assert llm_call_1.name == "litellm_request"
        assert llm_call_2.name == "litellm_request"

        assert llm_call_1.attributes is not None
        assert llm_call_1.attributes.get("gen_ai.prompt.0.role") == "system"
        assert llm_call_1.attributes.get("gen_ai.prompt.0.content") is not None
        assert llm_call_1.attributes.get("gen_ai.completion.0.role") == "assistant"
        assert llm_call_1.attributes.get("gen_ai.completion.0.content") == "hello world"

        assert llm_call_2.attributes is not None
        assert llm_call_2.attributes.get("gen_ai.prompt.0.role") == "system"
        assert llm_call_2.attributes.get("gen_ai.prompt.0.content") is not None
        assert llm_call_2.attributes.get("gen_ai.completion.0.role") == "assistant"
        assert llm_call_2.attributes.get("gen_ai.completion.0.content") == "hello world"
