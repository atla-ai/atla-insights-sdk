"""Test the lower-level span API."""

import json

from tests._otel import BaseLocalOtel


class TestSpan(BaseLocalOtel):
    """Test the span API."""

    def test_basic(self) -> None:
        """Test the span API."""
        from atla_insights.span import start_as_current_span

        with start_as_current_span("my-llm-generation") as atla_span:
            atla_span.record_generation(
                input_messages=[
                    {"role": "system", "content": "You are a helpful assistant."},
                    {"role": "user", "content": "What is the capital of France?"},
                ],
                output_messages=[
                    {"role": "assistant", "content": "The capital of France is Paris."},
                ],
            )

        spans = self.get_finished_spans()
        assert len(spans) == 1

        [span] = spans

        assert span.name == "my-llm-generation"
        assert span.attributes is not None

        assert span.attributes["llm.input_messages.0.message.role"] == "system"
        assert (
            span.attributes["llm.input_messages.0.message.content"]
            == "You are a helpful assistant."
        )
        assert span.attributes["llm.input_messages.1.message.role"] == "user"
        assert (
            span.attributes["llm.input_messages.1.message.content"]
            == "What is the capital of France?"
        )

        assert span.attributes["llm.output_messages.0.message.role"] == "assistant"
        assert (
            span.attributes["llm.output_messages.0.message.content"]
            == "The capital of France is Paris."
        )

    def test_tools(self) -> None:
        """Test the span API."""
        from atla_insights.span import start_as_current_span

        with start_as_current_span("my-llm-generation") as atla_span:
            atla_span.record_generation(
                input_messages=[
                    {"role": "system", "content": "You are a helpful assistant."},
                    {
                        "role": "user",
                        "content": "What are the capitals of France and Germany?",
                    },
                ],
                output_messages=[
                    {
                        "role": "assistant",
                        "tool_calls": [
                            {
                                "id": "1",
                                "type": "function",
                                "function": {
                                    "name": "get_capital",
                                    "arguments": '{"country": "France"}',
                                },
                            },
                            {
                                "id": "2",
                                "type": "function",
                                "function": {
                                    "name": "get_capital",
                                    "arguments": '{"country": "Germany"}',
                                },
                            },
                        ],
                    },
                ],
                tools=[
                    {
                        "type": "function",
                        "function": {
                            "name": "get_capital",
                            "description": "Get the capital of a country.",
                            "parameters": {
                                "type": "object",
                                "properties": {"country": {"type": "string"}},
                            },
                        },
                    },
                ],
            )

        spans = self.get_finished_spans()
        assert len(spans) == 1

        [span] = spans

        assert span.name == "my-llm-generation"
        assert span.attributes is not None

        assert span.attributes["llm.input_messages.0.message.role"] == "system"
        assert (
            span.attributes["llm.input_messages.0.message.content"]
            == "You are a helpful assistant."
        )
        assert span.attributes["llm.input_messages.1.message.role"] == "user"
        assert (
            span.attributes["llm.input_messages.1.message.content"]
            == "What are the capitals of France and Germany?"
        )

        assert span.attributes["llm.output_messages.0.message.role"] == "assistant"
        assert (
            span.attributes["llm.output_messages.0.message.tool_calls.0.tool_call.id"]
            == "1"
        )
        assert (
            span.attributes[
                "llm.output_messages.0.message.tool_calls.0.tool_call.function.name"
            ]
            == "get_capital"
        )
        assert (
            span.attributes[
                "llm.output_messages.0.message.tool_calls.0.tool_call.function.arguments"
            ]
            == '{"country": "France"}'
        )
        assert (
            span.attributes["llm.output_messages.0.message.tool_calls.1.tool_call.id"]
            == "2"
        )
        assert (
            span.attributes[
                "llm.output_messages.0.message.tool_calls.1.tool_call.function.name"
            ]
            == "get_capital"
        )
        assert (
            span.attributes[
                "llm.output_messages.0.message.tool_calls.1.tool_call.function.arguments"
            ]
            == '{"country": "Germany"}'
        )

        assert span.attributes["llm.tools.0.tool.json_schema"] == json.dumps(
            {
                "type": "function",
                "function": {
                    "name": "get_capital",
                    "description": "Get the capital of a country.",
                    "parameters": {
                        "type": "object",
                        "properties": {"country": {"type": "string"}},
                    },
                },
            }
        )
