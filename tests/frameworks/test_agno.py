"""Unit tests for the Agno instrumentation."""

from agno.agent import Agent
from agno.models.anthropic import Claude
from agno.models.google import Gemini
from agno.models.litellm import LiteLLM
from agno.models.openai import OpenAIChat
from agno.tools.function import Function, FunctionCall
from anthropic import Anthropic
from google.genai import Client
from openai import OpenAI

from tests._otel import BaseLocalOtel


class TestAgnoInstrumentation(BaseLocalOtel):
    """Test the Agno instrumentation."""

    def test_basic_with_openai(self, mock_openai_client: OpenAI) -> None:
        """Test the Agno instrumentation with OpenAI."""
        from atla_insights import instrument_agno

        with instrument_agno("openai"):
            agent = Agent(
                model=OpenAIChat(
                    id="mock-model",
                    base_url=str(mock_openai_client.base_url),
                    api_key="unit-test",
                ),
            )
            agent.run("Hello world!")

        finished_spans = self.get_finished_spans()

        assert len(finished_spans) == 3
        run, llm_call, request = finished_spans

        assert run.name == "Agent.run"
        assert llm_call.name == "OpenAIChat.invoke"
        assert request.name == "ChatCompletion"

        assert request.attributes is not None
        assert request.attributes.get("llm.input_messages.0.message.role") == "user"
        assert (
            request.attributes.get("llm.input_messages.0.message.content")
            == "Hello world!"
        )
        assert request.attributes.get("llm.output_messages.0.message.role") == "assistant"
        assert (
            request.attributes.get("llm.output_messages.0.message.content")
            == "hello world"
        )

    def test_basic_with_litellm(self, mock_openai_client: OpenAI) -> None:
        """Test the Agno instrumentation with LiteLLM."""
        from atla_insights import instrument_agno

        agent = Agent(
            model=LiteLLM(
                id="gpt-4o-mini",
                api_base=str(mock_openai_client.base_url),
                api_key="unit-test",
            ),
        )

        with instrument_agno("litellm"):
            agent.run("Hello world!")

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

    def test_basic_with_anthropic(self, mock_anthropic_client: Anthropic) -> None:
        """Test the Agno instrumentation with Anthropic."""
        from atla_insights import instrument_agno

        agent = Agent(
            model=Claude(
                id="some-model",
                client=mock_anthropic_client,
            ),
        )

        with instrument_agno("anthropic"):
            agent.run("Hello world!")

        finished_spans = self.get_finished_spans()

        assert len(finished_spans) == 3
        run, llm_call, request = finished_spans

        assert run.name == "Agent.run"
        assert llm_call.name == "Claude.invoke"
        assert request.name == "Messages"

        assert request.attributes is not None
        assert request.attributes.get("llm.input_messages.0.message.role") == "user"
        assert (
            request.attributes.get("llm.input_messages.0.message.content")
            == "Hello world!"
        )
        assert request.attributes.get("llm.output_messages.0.message.role") == "assistant"
        assert (
            request.attributes.get("llm.output_messages.0.message.content")
            == "Hi! My name is Claude."
        )

    def test_basic_with_google_genai(self, mock_google_genai_client: Client) -> None:
        """Test the Agno instrumentation with Google GenAI."""
        from atla_insights import instrument_agno

        agent = Agent(
            model=Gemini(
                id="some-model",
                client=mock_google_genai_client,
            ),
        )

        with instrument_agno("google-genai"):
            agent.run("Hello world!")

        finished_spans = self.get_finished_spans()

        assert len(finished_spans) == 3
        run, llm_call, request = finished_spans

        assert run.name == "Agent.run"
        assert llm_call.name == "Gemini.invoke"
        assert request.name == "GenerateContent"

        assert request.attributes is not None
        assert request.attributes.get("llm.input_messages.0.message.role") == "user"
        assert (
            request.attributes.get("llm.input_messages.0.message.content")
            == "Hello world!"
        )
        assert request.attributes.get("llm.output_messages.0.message.role") == "model"
        assert (
            request.attributes.get("llm.output_messages.0.message.content")
            == "hello world"
        )

    def test_multi(
        self, mock_openai_client: OpenAI, mock_anthropic_client: Anthropic
    ) -> None:
        """Test the Agno instrumentation with LiteLLM."""
        from atla_insights import instrument_agno

        anthropic_agent = Agent(
            model=Claude(
                id="some-model",
                client=mock_anthropic_client,
            ),
        )
        openai_agent = Agent(
            model=OpenAIChat(
                id="mock-model",
                base_url=str(mock_openai_client.base_url),
                api_key="unit-test",
            ),
        )

        with instrument_agno(["anthropic", "openai"]):
            anthropic_agent.run("Hello world!")
            openai_agent.run("Hello world!")

        finished_spans = self.get_finished_spans()

        assert len(finished_spans) == 6
        (
            anthropic_run,
            anthropic_llm_call,
            anthropic_request,
            openai_run,
            openai_llm_call,
            openai_request,
        ) = finished_spans

        assert anthropic_run.name == "Agent.run"
        assert anthropic_llm_call.name == "Claude.invoke"
        assert anthropic_request.name == "Messages"

        assert openai_run.name == "Agent.run"
        assert openai_llm_call.name == "OpenAIChat.invoke"
        assert openai_request.name == "ChatCompletion"

        assert anthropic_request.attributes is not None
        assert (
            anthropic_request.attributes.get("llm.input_messages.0.message.role")
            == "user"
        )
        assert (
            anthropic_request.attributes.get("llm.input_messages.0.message.content")
            == "Hello world!"
        )
        assert (
            anthropic_request.attributes.get("llm.output_messages.0.message.role")
            == "assistant"
        )
        assert (
            anthropic_request.attributes.get("llm.output_messages.0.message.content")
            == "Hi! My name is Claude."
        )

        assert openai_request.attributes is not None
        assert (
            openai_request.attributes.get("llm.input_messages.0.message.role") == "user"
        )
        assert (
            openai_request.attributes.get("llm.input_messages.0.message.content")
            == "Hello world!"
        )
        assert (
            openai_request.attributes.get("llm.output_messages.0.message.role")
            == "assistant"
        )
        assert (
            openai_request.attributes.get("llm.output_messages.0.message.content")
            == "hello world"
        )

    def test_tool_invocation(self) -> None:
        """Test the Agno instrumentation with tool invocation."""
        from atla_insights import instrument_agno

        with instrument_agno("openai"):
            fn = Function(
                name="test_function",
                description="Test function.",
                parameters={
                    "type": "object",
                    "properties": {"some-arg": {"type": "string"}},
                },
            )
            function_call = FunctionCall(
                function=fn,
                arguments={"some_arg": "some-value"},
                result="some-result",
                call_id="abc123",
            )
            function_call.execute()

        finished_spans = self.get_finished_spans()
        assert len(finished_spans) == 1

        [span] = finished_spans

        assert span.name == "test_function"

        assert span.attributes is not None

        assert span.attributes.get("openinference.span.kind") == "TOOL"

        assert span.attributes.get("tool.name") == "test_function"
        assert span.attributes.get("tool.description") == "Test function."
        assert span.attributes.get("tool.parameters") == '{"some_arg": "some-value"}'

        assert span.attributes.get("input.value") == '{"some_arg": "some-value"}'
        assert span.attributes.get("output.value") == "some-result"
