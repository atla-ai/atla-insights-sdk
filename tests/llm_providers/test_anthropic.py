"""Test the Anthropic instrumentation."""

import pytest
from anthropic import Anthropic, AnthropicBedrock, AsyncAnthropic, AsyncAnthropicBedrock

from tests._otel import BaseLocalOtel


class TestAnthropicInstrumentation(BaseLocalOtel):
    """Test the Anthropic instrumentation."""

    def test_basic(self, mock_anthropic_client: Anthropic) -> None:
        """Test basic Anthropic instrumentation."""
        from atla_insights import instrument_anthropic

        with instrument_anthropic():
            mock_anthropic_client.messages.create(
                model="some-model",
                max_tokens=1024,
                messages=[{"role": "user", "content": "Hello, Claude"}],
            )

        finished_spans = self.get_finished_spans()

        assert len(finished_spans) == 1
        [span] = finished_spans

        assert span.attributes is not None

        assert span.name == "Messages"

        assert span.attributes.get("llm.input_messages.0.message.role") == "user"
        assert (
            span.attributes.get("llm.input_messages.0.message.content") == "Hello, Claude"
        )

        assert span.attributes.get("llm.output_messages.0.message.role") == "assistant"
        assert (
            span.attributes.get("llm.output_messages.0.message.content")
            == "Hi! My name is Claude."
        )

    def test_basic_bedrock(self, mock_anthropic_bedrock_client: AnthropicBedrock) -> None:
        """Test basic Anthropic Bedrock instrumentation."""
        from atla_insights import instrument_anthropic

        with instrument_anthropic():
            mock_anthropic_bedrock_client.messages.create(
                model="some-model",
                max_tokens=1024,
                messages=[{"role": "user", "content": "Hello, Claude"}],
            )

        finished_spans = self.get_finished_spans()

        assert len(finished_spans) == 1
        [span] = finished_spans

        assert span.attributes is not None

        assert span.name == "Messages"

        assert span.attributes.get("llm.input_messages.0.message.role") == "user"
        assert (
            span.attributes.get("llm.input_messages.0.message.content") == "Hello, Claude"
        )

        assert span.attributes.get("llm.output_messages.0.message.role") == "assistant"
        assert (
            span.attributes.get("llm.output_messages.0.message.content")
            == "Hello! How are you doing today?"
        )

    def test_ctx(self, mock_anthropic_client: Anthropic) -> None:
        """Test basic Anthropic instrumentation."""
        from atla_insights import instrument_anthropic

        with instrument_anthropic():
            mock_anthropic_client.messages.create(
                model="some-model",
                max_tokens=1024,
                messages=[{"role": "user", "content": "Hello, Claude"}],
            )

        mock_anthropic_client.messages.create(
            model="some-model",
            max_tokens=1024,
            messages=[{"role": "user", "content": "Hello, Claude"}],
        )

        finished_spans = self.get_finished_spans()

        assert len(finished_spans) == 1

    @pytest.mark.asyncio
    async def test_async(self, mock_async_anthropic_client: AsyncAnthropic) -> None:
        """Test basic Anthropic instrumentation."""
        from atla_insights import instrument_anthropic

        with instrument_anthropic():
            await mock_async_anthropic_client.messages.create(
                model="some-model",
                max_tokens=1024,
                messages=[{"role": "user", "content": "Hello, Claude"}],
            )

        finished_spans = self.get_finished_spans()

        assert len(finished_spans) == 1
        [span] = finished_spans

        assert span.attributes is not None

        assert span.name == "AsyncMessages"

        assert span.attributes.get("llm.input_messages.0.message.role") == "user"
        assert (
            span.attributes.get("llm.input_messages.0.message.content") == "Hello, Claude"
        )

        assert span.attributes.get("llm.output_messages.0.message.role") == "assistant"
        assert (
            span.attributes.get("llm.output_messages.0.message.content")
            == "Hi! My name is Claude."
        )

    @pytest.mark.asyncio
    async def test_async_bedrock(
        self, mock_async_anthropic_bedrock_client: AsyncAnthropicBedrock
    ) -> None:
        """Test basic Anthropic Bedrock instrumentation."""
        from atla_insights import instrument_anthropic

        with instrument_anthropic():
            await mock_async_anthropic_bedrock_client.messages.create(
                model="some-model",
                max_tokens=1024,
                messages=[{"role": "user", "content": "Hello, Claude"}],
            )

        finished_spans = self.get_finished_spans()

        assert len(finished_spans) == 1
        [span] = finished_spans

        assert span.attributes is not None

        assert span.name == "AsyncMessages"

        assert span.attributes.get("llm.input_messages.0.message.role") == "user"
        assert (
            span.attributes.get("llm.input_messages.0.message.content") == "Hello, Claude"
        )

        assert span.attributes.get("llm.output_messages.0.message.role") == "assistant"
        assert (
            span.attributes.get("llm.output_messages.0.message.content")
            == "Hello! How are you doing today?"
        )
