"""Test the Anthropic instrumentation."""

import pytest
from google.genai import Client, types

from tests._otel import BaseLocalOtel


@pytest.mark.usefixtures("mock_google_genai_client")
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
