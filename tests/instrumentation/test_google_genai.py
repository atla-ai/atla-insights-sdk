"""Test the Google GenAI instrumentation."""

from typing import Iterable, Tuple

import pytest
from google.genai import Client, types
from opentelemetry.util.types import AttributeValue

from tests._otel import BaseLocalOtel


class TestGoogleGenAIInstrumentation(BaseLocalOtel):
    """Test the Google GenAI instrumentation."""

    def test_basic(self, mock_google_genai_client: Client) -> None:
        """Test basic Google GenAI instrumentation."""
        from src.atla_insights import instrument_google_genai

        with instrument_google_genai():
            mock_google_genai_client.models.generate_content(
                model="some-model",
                contents="Hello, World!",
            )

        finished_spans = self.get_finished_spans()

        assert len(finished_spans) == 1
        [span] = finished_spans

        assert span.attributes is not None

        assert span.name == "GenerateContent"

        assert span.attributes.get("llm.input_messages.0.message.role") == "user"
        assert (
            span.attributes.get("llm.input_messages.0.message.content") == "Hello, World!"
        )

        assert span.attributes.get("llm.output_messages.0.message.role") == "model"
        assert (
            span.attributes.get("llm.output_messages.0.message.content") == "hello world"
        )

    @pytest.mark.asyncio
    async def test_async(self, mock_google_genai_client: Client) -> None:
        """Test async Google GenAI instrumentation."""
        from src.atla_insights import instrument_google_genai

        with instrument_google_genai():
            await mock_google_genai_client.aio.models.generate_content(
                model="some-model",
                contents="Hello, World!",
            )

        finished_spans = self.get_finished_spans()

        assert len(finished_spans) == 1
        [span] = finished_spans

        assert span.attributes is not None

        assert span.name == "AsyncGenerateContent"

        assert span.attributes.get("llm.input_messages.0.message.role") == "user"
        assert (
            span.attributes.get("llm.input_messages.0.message.content") == "Hello, World!"
        )

        assert span.attributes.get("llm.output_messages.0.message.role") == "model"
        assert (
            span.attributes.get("llm.output_messages.0.message.content") == "hello world"
        )

    def test_tool_calls(self, mock_google_genai_client: Client) -> None:
        """Test Google GenAI instrumentation with tool calls."""
        from src.atla_insights import instrument_google_genai

        with instrument_google_genai():
            some_tool_function = types.FunctionDeclaration(
                name="some_tool",
                description="Some mock tool for unit testing.",
                parameters=types.Schema(
                    type=types.Type("object"),
                    properties={
                        "some_arg": types.Schema(
                            type=types.Type("string"),
                            description="Some mock argument",
                        ),
                    },
                    required=["some_arg"],
                ),
            )
            other_tool_function = types.FunctionDeclaration(
                name="other_tool",
                description="Another mock tool for unit testing.",
                parameters=types.Schema(
                    type=types.Type("object"),
                    properties={
                        "other_arg": types.Schema(
                            type=types.Type("string"),
                            description="Another mock argument",
                        ),
                    },
                    required=["other_arg"],
                ),
            )
            tools = types.Tool(
                function_declarations=[some_tool_function, other_tool_function],
            )
            config = types.GenerateContentConfig(tools=[tools])

            mock_google_genai_client.models.generate_content(
                model="some-tool-call-model",
                contents="Hello, World!",
                config=config,
            )

        finished_spans = self.get_finished_spans()

        assert len(finished_spans) == 1
        [span] = finished_spans

        assert span.attributes is not None

        assert span.name == "GenerateContent"

        assert span.attributes.get("llm.input_messages.0.message.role") == "user"
        assert (
            span.attributes.get("llm.input_messages.0.message.content") == "Hello, World!"
        )

        assert span.attributes.get("llm.output_messages.0.message.role") == "model"
        assert (
            span.attributes.get(
                "llm.output_messages.0.message.tool_calls.0.tool_call.function.arguments"
            )
            == '{"some_arg": "some value"}'
        )
        assert (
            span.attributes.get(
                "llm.output_messages.0.message.tool_calls.0.tool_call.function.name"
            )
            == "some_tool"
        )
        assert (
            span.attributes.get(
                "llm.output_messages.0.message.tool_calls.1.tool_call.function.arguments"
            )
            == '{"other_arg": "other value"}'
        )
        assert (
            span.attributes.get(
                "llm.output_messages.0.message.tool_calls.1.tool_call.function.name"
            )
            == "other_tool"
        )

        assert (
            span.attributes.get("llm.tools.0.tool.json_schema")
            == '{"type": "function", "function": {"name": "some_tool", "description": "Some mock tool for unit testing.", "parameters": {"type": "object", "properties": {"some_arg": {"type": "string", "description": "Some mock argument"}}, "required": ["some_arg"]}, "strict": null}}'  # noqa: E501
        )
        assert (
            span.attributes.get("llm.tools.1.tool.json_schema")
            == '{"type": "function", "function": {"name": "other_tool", "description": "Another mock tool for unit testing.", "parameters": {"type": "object", "properties": {"other_arg": {"type": "string", "description": "Another mock argument"}}, "required": ["other_arg"]}, "strict": null}}'  # noqa: E501
        )


class TestGoogleGenAIInstrumentationHelpers:
    """Test the Google GenAI instrumentation helpers."""

    @pytest.mark.parametrize(
        "content_parts, expected",
        [
            pytest.param(
                [
                    types.Part(
                        function_call=types.FunctionCall(
                            name="some_tool", args={"some_arg": "some value"}
                        )
                    )
                ],
                [
                    (
                        "message.tool_calls.0.tool_call.function.arguments",
                        '{"some_arg": "some value"}',
                    ),
                    ("message.tool_calls.0.tool_call.function.name", "some_tool"),
                ],
                id="single_tool_call",
            ),
        ],
    )
    def test_get_tool_calls_from_content_parts(
        self,
        content_parts: Iterable[object],
        expected: Iterable[Tuple[str, AttributeValue]],
    ) -> None:
        """Test the get_tool_calls_from_content_parts function."""
        from src.atla_insights._google_genai import _get_tool_calls_from_content_parts

        tool_calls = _get_tool_calls_from_content_parts(content_parts)

        assert sorted(tool_calls) == sorted(expected)
