"""Unit tests for the Agno instrumentation."""

import pytest
from agno.agent import Agent
from agno.models.anthropic import Claude
from agno.models.google import Gemini
from agno.models.litellm import LiteLLM
from agno.models.openai import OpenAIChat
from agno.team import Team
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

    def test_multi_agent(self, mock_openai_client: OpenAI) -> None:
        """Test multi-agent name tracking."""
        from atla_insights import instrument_agno

        my_agent = Agent(
            name="my-agent",
            model=OpenAIChat(
                id="mock-model",
                base_url=str(mock_openai_client.base_url),
                api_key="unit-test",
            ),
        )
        other_agent = Agent(
            name="other-agent",
            model=OpenAIChat(
                id="mock-model",
                base_url=str(mock_openai_client.base_url),
                api_key="unit-test",
            ),
        )

        with instrument_agno("openai"):
            my_agent.run("Hello world!")
            other_agent.run("Hello world!")

        finished_spans = self.get_finished_spans()

        assert len(finished_spans) == 6
        my_agent_run, _, _, other_agent_run, _, _ = finished_spans

        assert my_agent_run.attributes is not None
        assert my_agent_run.attributes.get("graph.node.id") is not None
        assert my_agent_run.attributes.get("graph.node.name") == "my-agent"

        assert other_agent_run.attributes is not None
        assert other_agent_run.attributes.get("graph.node.id") is not None
        assert other_agent_run.attributes.get("graph.node.name") == "other-agent"

    def test_tool_invocation(self) -> None:
        """Test the Agno instrumentation with tool invocation."""
        from atla_insights import instrument_agno

        with instrument_agno("openai"):

            def test_function(some_arg: str) -> str:
                """Test function."""
                return "some-result"

            function_call = FunctionCall(
                function=Function.from_callable(test_function),
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

    def test_stream(self, mock_openai_stream_client: OpenAI) -> None:
        """Test the Agno instrumentation with OpenAI."""
        from atla_insights import instrument_agno

        with instrument_agno("openai"):
            agent = Agent(
                model=OpenAIChat(
                    id="mock-model",
                    base_url=str(mock_openai_stream_client.base_url),
                    api_key="unit-test",
                ),
            )

            for _ in agent.run("Hello world!", stream=True):
                pass

        finished_spans = self.get_finished_spans()

        assert len(finished_spans) == 3
        run, llm_call, request = finished_spans

        assert run.name == "Agent.run"
        assert llm_call.name == "OpenAIChat.invoke_stream"
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

    @pytest.mark.asyncio
    async def test_async(self, mock_openai_client: OpenAI) -> None:
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

            await agent.arun("Hello world!")

        finished_spans = self.get_finished_spans()

        assert len(finished_spans) == 3
        run, llm_call, request = finished_spans

        assert run.name == "Agent.arun"
        assert llm_call.name == "OpenAIChat.ainvoke"
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

    @pytest.mark.asyncio
    async def test_async_stream(self, mock_async_openai_stream_client: OpenAI) -> None:
        """Test the Agno instrumentation with OpenAI."""
        from atla_insights import instrument_agno

        with instrument_agno("openai"):
            agent = Agent(
                model=OpenAIChat(
                    id="mock-model",
                    base_url=str(mock_async_openai_stream_client.base_url),
                    api_key="unit-test",
                ),
            )

            async for _ in agent.arun("Hello world!", stream=True):
                pass

        finished_spans = self.get_finished_spans()

        assert len(finished_spans) == 3
        run, llm_call, request = finished_spans

        assert run.name == "Agent.arun"
        assert llm_call.name == "OpenAIChat.ainvoke_stream"
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

    def test_team(self, mock_openai_client: OpenAI) -> None:
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

            team = Team(
                members=[agent],
                model=OpenAIChat(
                    id="mock-model",
                    base_url=str(mock_openai_client.base_url),
                    api_key="unit-test",
                ),
            )

            team.run("Hello world!")

        finished_spans = self.get_finished_spans()

        assert len(finished_spans) == 3
        run, llm_call, request = finished_spans

        assert run.name == "Team.run"
        assert llm_call.name == "OpenAIChat.invoke"
        assert request.name == "ChatCompletion"

        assert request.attributes is not None
        assert request.attributes.get("llm.input_messages.0.message.role") == "developer"
        assert request.attributes.get("llm.input_messages.0.message.content") is not None
        assert request.attributes.get("llm.input_messages.1.message.role") == "user"
        assert (
            request.attributes.get("llm.input_messages.1.message.content")
            == "Hello world!"
        )
        assert request.attributes.get("llm.output_messages.0.message.role") == "assistant"
        assert (
            request.attributes.get("llm.output_messages.0.message.content")
            == "hello world"
        )

    def test_team_stream(self, mock_openai_stream_client: OpenAI) -> None:
        """Test the Agno instrumentation with OpenAI."""
        from atla_insights import instrument_agno

        with instrument_agno("openai"):
            agent = Agent(
                model=OpenAIChat(
                    id="mock-model",
                    base_url=str(mock_openai_stream_client.base_url),
                    api_key="unit-test",
                ),
            )

            team = Team(
                members=[agent],
                model=OpenAIChat(
                    id="mock-model",
                    base_url=str(mock_openai_stream_client.base_url),
                    api_key="unit-test",
                ),
            )

            for _ in team.run("Hello world!", stream=True):
                pass

        finished_spans = self.get_finished_spans()

        assert len(finished_spans) == 3
        run, llm_call, request = finished_spans

        assert run.name == "Team.run"
        assert llm_call.name == "OpenAIChat.invoke_stream"
        assert request.name == "ChatCompletion"

        assert request.attributes is not None
        assert request.attributes.get("llm.input_messages.0.message.role") == "developer"
        assert request.attributes.get("llm.input_messages.0.message.content") is not None
        assert request.attributes.get("llm.input_messages.1.message.role") == "user"
        assert (
            request.attributes.get("llm.input_messages.1.message.content")
            == "Hello world!"
        )
        assert request.attributes.get("llm.output_messages.0.message.role") == "assistant"
        assert (
            request.attributes.get("llm.output_messages.0.message.content")
            == "hello world"
        )

    @pytest.mark.asyncio
    async def test_team_async(self, mock_async_openai_client: OpenAI) -> None:
        """Test the Agno instrumentation with OpenAI."""
        from atla_insights import instrument_agno

        with instrument_agno("openai"):
            agent = Agent(
                model=OpenAIChat(
                    id="mock-model",
                    base_url=str(mock_async_openai_client.base_url),
                    api_key="unit-test",
                ),
            )

            team = Team(
                members=[agent],
                model=OpenAIChat(
                    id="mock-model",
                    base_url=str(mock_async_openai_client.base_url),
                    api_key="unit-test",
                ),
            )

            await team.arun("Hello world!")

        finished_spans = self.get_finished_spans()

        assert len(finished_spans) == 3
        run, llm_call, request = finished_spans

        assert run.name == "Team.arun"
        assert llm_call.name == "OpenAIChat.ainvoke"
        assert request.name == "ChatCompletion"

        assert request.attributes is not None
        assert request.attributes.get("llm.input_messages.0.message.role") == "developer"
        assert request.attributes.get("llm.input_messages.0.message.content") is not None
        assert request.attributes.get("llm.input_messages.1.message.role") == "user"
        assert (
            request.attributes.get("llm.input_messages.1.message.content")
            == "Hello world!"
        )
        assert request.attributes.get("llm.output_messages.0.message.role") == "assistant"
        assert (
            request.attributes.get("llm.output_messages.0.message.content")
            == "hello world"
        )

    @pytest.mark.asyncio
    async def test_team_async_stream(
        self, mock_async_openai_stream_client: OpenAI
    ) -> None:
        """Test the Agno instrumentation with OpenAI."""
        from atla_insights import instrument_agno

        with instrument_agno("openai"):
            agent = Agent(
                model=OpenAIChat(
                    id="mock-model",
                    base_url=str(mock_async_openai_stream_client.base_url),
                    api_key="unit-test",
                ),
            )

            team = Team(
                members=[agent],
                model=OpenAIChat(
                    id="mock-model",
                    base_url=str(mock_async_openai_stream_client.base_url),
                    api_key="unit-test",
                ),
            )

            async for _ in team.arun("Hello world!", stream=True):
                pass

        finished_spans = self.get_finished_spans()

        assert len(finished_spans) == 3
        run, llm_call, request = finished_spans

        assert run.name == "Team.arun"
        assert llm_call.name == "OpenAIChat.ainvoke_stream"
        assert request.name == "ChatCompletion"

        assert request.attributes is not None
        assert request.attributes.get("llm.input_messages.0.message.role") == "developer"
        assert request.attributes.get("llm.input_messages.0.message.content") is not None
        assert request.attributes.get("llm.input_messages.1.message.role") == "user"
        assert (
            request.attributes.get("llm.input_messages.1.message.content")
            == "Hello world!"
        )
        assert request.attributes.get("llm.output_messages.0.message.role") == "assistant"
        assert (
            request.attributes.get("llm.output_messages.0.message.content")
            == "hello world"
        )
