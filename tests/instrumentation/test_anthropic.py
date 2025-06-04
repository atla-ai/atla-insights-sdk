"""Test the Anthropic instrumentation."""

import pytest
from anthropic import Anthropic

from tests._otel import BaseLocalOtel


@pytest.mark.usefixtures("mock_anthropic_client")
class TestAnthropicInstrumentation(BaseLocalOtel):
    """Test the Anthropic instrumentation."""

    def test_basic(self, mock_anthropic_client: Anthropic) -> None:
        """Test basic Anthropic instrumentation."""
        from src.atla_insights import instrument_anthropic

        instrument_anthropic()

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
