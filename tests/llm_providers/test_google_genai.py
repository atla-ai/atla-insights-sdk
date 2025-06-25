"""Test the Google GenAI instrumentation."""

from typing import Any, Iterable, Iterator, Mapping, Tuple

import pytest
from google.genai import Client, types
from opentelemetry.util.types import AttributeValue

from tests._otel import BaseLocalOtel


class TestGoogleGenAIInstrumentation(BaseLocalOtel):
    """Test the Google GenAI instrumentation."""

    def test_basic(self, mock_google_genai_client: Client) -> None:
        """Test basic Google GenAI instrumentation."""
        from atla_insights import instrument_google_genai

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
        from atla_insights import instrument_google_genai

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
        from atla_insights import instrument_google_genai

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
            pytest.param(
                [
                    types.Part(
                        function_call=types.FunctionCall(
                            name="some_tool", args={"some_arg": "some value"}
                        )
                    ),
                    types.Part(
                        function_call=types.FunctionCall(
                            name="other_tool", args={"other_arg": "other value"}
                        )
                    ),
                ],
                [
                    (
                        "message.tool_calls.0.tool_call.function.arguments",
                        '{"some_arg": "some value"}',
                    ),
                    ("message.tool_calls.0.tool_call.function.name", "some_tool"),
                    (
                        "message.tool_calls.1.tool_call.function.arguments",
                        '{"other_arg": "other value"}',
                    ),
                    ("message.tool_calls.1.tool_call.function.name", "other_tool"),
                ],
                id="multi_tool_call",
            ),
        ],
    )
    def test_get_tool_calls_from_content_parts(
        self,
        content_parts: Iterable[object],
        expected: Iterable[Tuple[str, AttributeValue]],
    ) -> None:
        """Test the get_tool_calls_from_content_parts function."""
        from atla_insights.llm_providers.instrumentors.google_genai import (
            _get_tool_calls_from_content_parts,
        )

        tool_calls = _get_tool_calls_from_content_parts(content_parts)
        assert sorted(tool_calls) == sorted(expected)

    @pytest.mark.parametrize(
        "request_parameters, expected",
        [
            pytest.param(
                {
                    "config": types.GenerateContentConfig(
                        tools=[
                            types.Tool(
                                function_declarations=[
                                    types.FunctionDeclaration(
                                        name="some_tool",
                                        description="Some mock tool for unit testing.",
                                        parameters=types.Schema(
                                            type=types.Type("object"),
                                        ),
                                    )
                                ]
                            )
                        ]
                    )
                },
                [
                    (
                        "llm.tools.0.tool.json_schema",
                        '{"type": "function", "function": {"name": "some_tool", "description": "Some mock tool for unit testing.", "parameters": {"type": "object"}, "strict": null}}',  # noqa: E501
                    ),
                ],
                id="single_function_declaration",
            ),
            pytest.param(
                {
                    "config": types.GenerateContentConfig(
                        tools=[
                            types.Tool(
                                function_declarations=[
                                    types.FunctionDeclaration(
                                        name="tool_1",
                                        description="First test tool",
                                        parameters=types.Schema(
                                            type=types.Type("object"),
                                        ),
                                    ),
                                    types.FunctionDeclaration(
                                        name="tool_2",
                                        description="Second test tool",
                                        parameters=types.Schema(
                                            type=types.Type("object"),
                                        ),
                                    ),
                                ]
                            )
                        ]
                    )
                },
                [
                    (
                        "llm.tools.0.tool.json_schema",
                        '{"type": "function", "function": {"name": "tool_1", "description": "First test tool", "parameters": {"type": "object"}, "strict": null}}',  # noqa: E501
                    ),
                    (
                        "llm.tools.1.tool.json_schema",
                        '{"type": "function", "function": {"name": "tool_2", "description": "Second test tool", "parameters": {"type": "object"}, "strict": null}}',  # noqa: E501
                    ),
                ],
                id="multiple_function_declarations",
            ),
            pytest.param(
                {
                    "contents": [
                        types.Content(
                            parts=[
                                types.Part(
                                    function_call=types.FunctionCall(
                                        name="test_function", args={"arg1": "value1"}
                                    )
                                )
                            ]
                        )
                    ]
                },
                [
                    ("llm.input_messages.0.message.role", "model"),
                    (
                        "llm.input_messages.0.message.tool_calls.0.tool_call.function.name",
                        "test_function",
                    ),
                    (
                        "llm.input_messages.0.message.tool_calls.0.tool_call.function.arguments",
                        '{"arg1": "value1"}',
                    ),
                ],
                id="single_function_call",
            ),
            pytest.param(
                {
                    "contents": [
                        types.Content(
                            parts=[
                                types.Part(
                                    function_response=types.FunctionResponse(
                                        response={"result": "test result"}
                                    )
                                )
                            ]
                        )
                    ]
                },
                [
                    ("llm.input_messages.0.message.role", "tool"),
                    ("llm.input_messages.0.message.content", "test result"),
                ],
                id="function_response",
            ),
            pytest.param(
                {
                    "contents": [
                        types.Content(
                            parts=[
                                types.Part(
                                    function_response=types.FunctionResponse(
                                        response={"result": "test result"}
                                    )
                                ),
                                types.Part(
                                    function_response=types.FunctionResponse(
                                        response={"result": "other result"}
                                    )
                                ),
                            ]
                        )
                    ]
                },
                [
                    ("llm.input_messages.0.message.role", "tool"),
                    ("llm.input_messages.0.message.content", "test result"),
                    ("llm.input_messages.1.message.role", "tool"),
                    ("llm.input_messages.1.message.content", "other result"),
                ],
                id="multiple_function_responses",
            ),
            pytest.param(
                {
                    "contents": [
                        types.Content(
                            parts=[
                                types.Part(
                                    function_call=types.FunctionCall(
                                        name="func1", args={"x": 1}
                                    )
                                ),
                                types.Part(
                                    function_call=types.FunctionCall(
                                        name="func2", args={"y": 2}
                                    )
                                ),
                            ]
                        )
                    ]
                },
                [
                    ("llm.input_messages.0.message.role", "model"),
                    (
                        "llm.input_messages.0.message.tool_calls.0.tool_call.function.name",
                        "func1",
                    ),
                    (
                        "llm.input_messages.0.message.tool_calls.0.tool_call.function.arguments",
                        '{"x": 1}',
                    ),
                    (
                        "llm.input_messages.0.message.tool_calls.1.tool_call.function.name",
                        "func2",
                    ),
                    (
                        "llm.input_messages.0.message.tool_calls.1.tool_call.function.arguments",
                        '{"y": 2}',
                    ),
                ],
                id="multiple_function_calls",
            ),
        ],
    )
    def test_get_tools_from_request(
        self,
        request_parameters: Mapping[str, Any],
        expected: Iterator[Tuple[str, AttributeValue]],
    ) -> None:
        """Test the get_tools_from_request function."""
        from atla_insights.llm_providers.instrumentors.google_genai import (
            get_tools_from_request,
        )

        tools = get_tools_from_request(request_parameters)
        assert sorted(tools) == sorted(expected)
