"""Unit tests for the SmolAgents instrumentation."""

from openai import OpenAI
from smolagents import CodeAgent, LiteLLMModel, OpenAIServerModel, tool

from tests._otel import BaseLocalOtel


class TestSmolAgentsInstrumentation(BaseLocalOtel):
    """Test the SmolAgents instrumentation."""

    def test_basic_with_openai(self, mock_openai_client: OpenAI) -> None:
        """Test the SmolAgents instrumentation with OpenAI."""
        from atla_insights import instrument_smolagents

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

        assert len(finished_spans) == 7
        run, _, invoke_1, llm_call_1, _, invoke_2, llm_call_2 = finished_spans

        assert run.name == "CodeAgent.run"
        assert invoke_1.name == "OpenAIServerModel.generate"
        assert llm_call_1.name == "ChatCompletion"
        assert invoke_2.name == "OpenAIServerModel.generate"
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
        from atla_insights import instrument_smolagents

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

        assert len(finished_spans) == 5
        run, invoke_1, llm_call_1, invoke_2, llm_call_2 = finished_spans

        assert run.name == "CodeAgent.run"
        assert invoke_1.name == "LiteLLMModel.generate"
        assert llm_call_1.name == "litellm_request"
        assert invoke_2.name == "LiteLLMModel.generate"
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

    def test_tool_invocation(self) -> None:
        """Test the SmolAgents instrumentation with tool invocation."""
        from atla_insights import instrument_smolagents

        with instrument_smolagents("openai"):

            @tool
            def some_function(some_arg: str) -> str:
                """Test function.

                Args:
                    some_arg: Some arg.

                Returns:
                    Some result.
                """
                return "some-result"

            some_function(some_arg="some-value")

        finished_spans = self.get_finished_spans()
        assert len(finished_spans) == 1

        [span] = finished_spans

        assert span.name == "some_function"

        assert span.attributes is not None

        assert span.attributes.get("openinference.span.kind") == "TOOL"

        assert span.attributes.get("tool.name") == "some_function"
        assert span.attributes.get("tool.description") == "Test function."
        assert span.attributes.get("tool.parameters") == '{"some_arg": "some-value"}'

        assert span.attributes.get("input.value") is not None
        assert span.attributes.get("output.value") == "some-result"
