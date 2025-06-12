"""Unit tests for the SmolAgents instrumentation."""

from openai import OpenAI
from smolagents import CodeAgent, LiteLLMModel, OpenAIServerModel

from tests._otel import BaseLocalOtel


class TestSmolAgentsInstrumentation(BaseLocalOtel):
    """Test the SmolAgents instrumentation."""

    def test_basic_with_openai(self, mock_openai_client: OpenAI) -> None:
        """Test the SmolAgents instrumentation with OpenAI."""
        from src.atla_insights import instrument_smolagents

        agent = CodeAgent(
            model=OpenAIServerModel(
                model_id="mock-model",
                api_base=str(mock_openai_client.base_url),
                api_key="unit-test",
            ),
            tools=[],
        )

        with instrument_smolagents("openai"):
            agent.run("Hello world!", max_steps=1)

        finished_spans = self.get_finished_spans()

        assert len(finished_spans) == 3
        run, llm_call_1, llm_call_2 = finished_spans

        assert run.name == "CodeAgent.run"
        assert llm_call_1.name == "ChatCompletion"
        assert llm_call_2.name == "ChatCompletion"

        assert llm_call_1.attributes is not None
        assert llm_call_1.attributes.get("llm.input_messages.0.message.role") == "system"
        assert (
            llm_call_1.attributes.get(
                "llm.input_messages.0.message.contents.0.message_content.text"
            )
            is not None
        )
        assert llm_call_1.attributes.get("llm.input_messages.1.message.role") == "user"
        assert (
            llm_call_1.attributes.get(
                "llm.input_messages.1.message.contents.0.message_content.text"
            )
            is not None
        )
        assert (
            llm_call_1.attributes.get("llm.output_messages.0.message.role") == "assistant"
        )
        assert (
            llm_call_1.attributes.get("llm.output_messages.0.message.content")
            == "hello world"
        )

        assert llm_call_2.attributes is not None
        assert llm_call_2.attributes.get("llm.input_messages.0.message.role") == "system"
        assert (
            llm_call_2.attributes.get(
                "llm.input_messages.0.message.contents.0.message_content.text"
            )
            is not None
        )
        assert llm_call_2.attributes.get("llm.input_messages.1.message.role") == "user"
        assert (
            llm_call_2.attributes.get(
                "llm.input_messages.1.message.contents.0.message_content.text"
            )
            is not None
        )
        assert (
            llm_call_2.attributes.get("llm.output_messages.0.message.role") == "assistant"
        )
        assert (
            llm_call_2.attributes.get("llm.output_messages.0.message.content")
            == "hello world"
        )

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

        with instrument_smolagents("litellm"):
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
