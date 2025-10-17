"""Unit tests for the Pydantic AI instrumentation."""

import pytest
from anthropic import AsyncAnthropic
from openai import AsyncOpenAI
from pydantic_ai import Agent
from pydantic_ai.models.anthropic import AnthropicModel
from pydantic_ai.models.openai import OpenAIChatModel
from pydantic_ai.providers.anthropic import AnthropicProvider
from pydantic_ai.providers.openai import OpenAIProvider

from tests._otel import BaseLocalOtel


class TestPydanticAIInstrumentation(BaseLocalOtel):
    """Test the Pydantic AI instrumentation."""

    def test_basic_with_openai(self, mock_async_openai_client: AsyncOpenAI) -> None:
        """Test the Pydantic AI instrumentation with OpenAI."""
        from atla_insights import instrument_pydantic_ai

        mock_model_name = "mock-model"

        agent = Agent(
            model=OpenAIChatModel(
                model_name=mock_model_name,
                provider=OpenAIProvider(openai_client=mock_async_openai_client),
            ),
            system_prompt="You are a helpful assistant.",
            instrument=True,
        )

        with instrument_pydantic_ai():
            agent.run_sync("Hello world!")

        finished_spans = self.get_finished_spans()

        assert len(finished_spans) == 2

        agent_run, llm_call = finished_spans

        assert agent_run.name == "agent run"

        assert llm_call.name == f"chat {mock_model_name}"
        assert llm_call.attributes is not None

        assert llm_call.attributes.get("llm.input_messages.0.message.role") == "system"
        assert (
            llm_call.attributes.get("llm.input_messages.0.message.content")
            == "You are a helpful assistant."
        )
        assert llm_call.attributes.get("llm.input_messages.1.message.role") == "user"
        assert (
            llm_call.attributes.get("llm.input_messages.1.message.content")
            == "Hello world!"
        )
        assert (
            llm_call.attributes.get("llm.output_messages.0.message.role") == "assistant"
        )
        assert (
            llm_call.attributes.get("llm.output_messages.0.message.content")
            == "hello world"
        )

    def test_basic_with_anthropic(
        self, mock_async_anthropic_client: AsyncAnthropic
    ) -> None:
        """Test the Pydantic AI instrumentation with Anthropic."""
        from atla_insights import instrument_pydantic_ai

        mock_model_name = "mock-model"

        agent = Agent(
            model=AnthropicModel(
                model_name=mock_model_name,
                provider=AnthropicProvider(anthropic_client=mock_async_anthropic_client),
            ),
            system_prompt="You are a helpful assistant.",
            instrument=True,
        )

        with instrument_pydantic_ai():
            agent.run_sync("Hello world!")

        finished_spans = self.get_finished_spans()

        assert len(finished_spans) == 2

        agent_run, llm_call = finished_spans

        assert agent_run.name == "agent run"

        assert llm_call.name == f"chat {mock_model_name}"
        assert llm_call.attributes is not None

        assert llm_call.attributes.get("llm.input_messages.0.message.role") == "system"
        assert (
            llm_call.attributes.get("llm.input_messages.0.message.content")
            == "You are a helpful assistant."
        )
        assert llm_call.attributes.get("llm.input_messages.1.message.role") == "user"
        assert (
            llm_call.attributes.get("llm.input_messages.1.message.content")
            == "Hello world!"
        )
        assert (
            llm_call.attributes.get("llm.output_messages.0.message.role") == "assistant"
        )
        assert (
            llm_call.attributes.get("llm.output_messages.0.message.content")
            == "Hi! My name is Claude."
        )

    @pytest.mark.asyncio
    async def test_async_with_openai(self, mock_async_openai_client: AsyncOpenAI) -> None:
        """Test the async Pydantic AI instrumentation with OpenAI."""
        from atla_insights import instrument_pydantic_ai

        mock_model_name = "mock-model"

        agent = Agent(
            model=OpenAIChatModel(
                model_name=mock_model_name,
                provider=OpenAIProvider(openai_client=mock_async_openai_client),
            ),
            system_prompt="You are a helpful assistant.",
            instrument=True,
        )

        with instrument_pydantic_ai():
            await agent.run("Hello world!")

        finished_spans = self.get_finished_spans()

        assert len(finished_spans) == 2

        agent_run, llm_call = finished_spans

        assert agent_run.name == "agent run"

        assert llm_call.name == f"chat {mock_model_name}"
        assert llm_call.attributes is not None

        assert llm_call.attributes.get("llm.input_messages.0.message.role") == "system"
        assert (
            llm_call.attributes.get("llm.input_messages.0.message.content")
            == "You are a helpful assistant."
        )
        assert llm_call.attributes.get("llm.input_messages.1.message.role") == "user"
        assert (
            llm_call.attributes.get("llm.input_messages.1.message.content")
            == "Hello world!"
        )
        assert (
            llm_call.attributes.get("llm.output_messages.0.message.role") == "assistant"
        )
        assert (
            llm_call.attributes.get("llm.output_messages.0.message.content")
            == "hello world"
        )

    @pytest.mark.asyncio
    async def test_async_with_anthropic(
        self, mock_async_anthropic_client: AsyncAnthropic
    ) -> None:
        """Test the async Pydantic AI instrumentation with Anthropic."""
        from atla_insights import instrument_pydantic_ai

        mock_model_name = "mock-model"

        agent = Agent(
            model=AnthropicModel(
                model_name=mock_model_name,
                provider=AnthropicProvider(anthropic_client=mock_async_anthropic_client),
            ),
            system_prompt="You are a helpful assistant.",
            instrument=True,
        )

        with instrument_pydantic_ai():
            await agent.run("Hello world!")

        finished_spans = self.get_finished_spans()

        assert len(finished_spans) == 2

        agent_run, llm_call = finished_spans

        assert agent_run.name == "agent run"

        assert llm_call.name == f"chat {mock_model_name}"
        assert llm_call.attributes is not None

        assert llm_call.attributes.get("llm.input_messages.0.message.role") == "system"
        assert (
            llm_call.attributes.get("llm.input_messages.0.message.content")
            == "You are a helpful assistant."
        )
        assert llm_call.attributes.get("llm.input_messages.1.message.role") == "user"
        assert (
            llm_call.attributes.get("llm.input_messages.1.message.content")
            == "Hello world!"
        )
        assert (
            llm_call.attributes.get("llm.output_messages.0.message.role") == "assistant"
        )
        assert (
            llm_call.attributes.get("llm.output_messages.0.message.content")
            == "Hi! My name is Claude."
        )

    def test_non_explicit_instrument(self, mock_async_openai_client: AsyncOpenAI) -> None:
        """Test non-explicit instrumentation in Pydantic AI instrumentation."""
        from atla_insights import instrument_pydantic_ai

        mock_model_name = "mock-model"

        agent = Agent(
            model=OpenAIChatModel(
                model_name=mock_model_name,
                provider=OpenAIProvider(openai_client=mock_async_openai_client),
            ),
            system_prompt="You are a helpful assistant.",
        )

        with instrument_pydantic_ai():
            agent.run_sync("Hello world!")

        finished_spans = self.get_finished_spans()

        assert len(finished_spans) == 2

    @pytest.mark.asyncio
    async def test_streaming_with_openai(
        self, mock_async_openai_stream_client: AsyncOpenAI
    ) -> None:
        """Test the streaming Pydantic AI instrumentation with OpenAI."""
        from atla_insights import instrument_pydantic_ai

        mock_model_name = "mock-model"

        agent = Agent(
            model=OpenAIChatModel(
                model_name=mock_model_name,
                provider=OpenAIProvider(openai_client=mock_async_openai_stream_client),
            ),
            system_prompt="You are a helpful assistant.",
            instrument=True,
        )

        with instrument_pydantic_ai():
            async with agent.run_stream("Hello world!"):
                ...

        finished_spans = self.get_finished_spans()

        assert len(finished_spans) == 2

        agent_run, llm_call = finished_spans

        assert agent_run.name == "agent run"

        assert llm_call.name == f"chat {mock_model_name}"
        assert llm_call.attributes is not None

        assert llm_call.attributes.get("llm.input_messages.0.message.role") == "system"
        assert (
            llm_call.attributes.get("llm.input_messages.0.message.content")
            == "You are a helpful assistant."
        )
        assert llm_call.attributes.get("llm.input_messages.1.message.role") == "user"
        assert (
            llm_call.attributes.get("llm.input_messages.1.message.content")
            == "Hello world!"
        )
        assert (
            llm_call.attributes.get("llm.output_messages.0.message.role") == "assistant"
        )
        assert (
            llm_call.attributes.get("llm.output_messages.0.message.content")
            == "hello world"
        )

    @pytest.mark.asyncio
    async def test_streaming_with_anthropic(
        self, mock_async_anthropic_stream_client: AsyncAnthropic
    ) -> None:
        """Test the streaming Pydantic AI instrumentation with Anthropic."""
        from atla_insights import instrument_pydantic_ai

        mock_model_name = "mock-model"

        agent = Agent(
            model=AnthropicModel(
                model_name=mock_model_name,
                provider=AnthropicProvider(
                    anthropic_client=mock_async_anthropic_stream_client
                ),
            ),
            system_prompt="You are a helpful assistant.",
            instrument=True,
        )

        with instrument_pydantic_ai():
            async with agent.run_stream("Hello world!"):
                ...

        finished_spans = self.get_finished_spans()

        assert len(finished_spans) == 2

        agent_run, llm_call = finished_spans

        assert agent_run.name == "agent run"

        assert llm_call.name == f"chat {mock_model_name}"
        assert llm_call.attributes is not None

        assert llm_call.attributes.get("llm.input_messages.0.message.role") == "system"
        assert (
            llm_call.attributes.get("llm.input_messages.0.message.content")
            == "You are a helpful assistant."
        )
        assert llm_call.attributes.get("llm.input_messages.1.message.role") == "user"
        assert (
            llm_call.attributes.get("llm.input_messages.1.message.content")
            == "Hello world!"
        )
        assert (
            llm_call.attributes.get("llm.output_messages.0.message.role") == "assistant"
        )
        assert (
            llm_call.attributes.get("llm.output_messages.0.message.content")
            == "Hi! My name is Claude."
        )

    def test_context_manager(self, mock_async_openai_client: AsyncOpenAI) -> None:
        """Test Pydantic AI instrumentation context manager."""
        from atla_insights import instrument_pydantic_ai

        mock_model_name = "mock-model"

        agent = Agent(
            model=OpenAIChatModel(
                model_name=mock_model_name,
                provider=OpenAIProvider(openai_client=mock_async_openai_client),
            ),
            system_prompt="You are a helpful assistant.",
        )

        # This call should not get picked up
        agent.run_sync("Hello world!")

        with instrument_pydantic_ai():
            agent.run_sync("Hello world!")

        # This call should not get picked up
        agent.run_sync("Hello world!")

        finished_spans = self.get_finished_spans()

        assert len(finished_spans) == 2
