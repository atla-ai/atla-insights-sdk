"""Fixtures for the tests."""

import io
import json
from pathlib import Path
from typing import Any, AsyncGenerator, Callable, Generator, Tuple
from unittest.mock import AsyncMock, patch

import boto3
import claude_agent_sdk._internal.query
import claude_agent_sdk._internal.transport.subprocess_cli
import claude_agent_sdk.client
import claude_code_sdk._internal.query
import claude_code_sdk._internal.transport.subprocess_cli
import claude_code_sdk.client
import pytest
from anthropic import Anthropic, AnthropicBedrock, AsyncAnthropic, AsyncAnthropicBedrock
from botocore.client import BaseClient
from botocore.response import StreamingBody
from botocore.stub import ANY, Stubber
from google.genai import Client
from google.genai.types import HttpOptions
from openai import AsyncAzureOpenAI, AsyncOpenAI, AzureOpenAI, OpenAI
from opentelemetry.sdk.trace.export.in_memory_span_exporter import InMemorySpanExporter
from pytest_httpserver import HTTPServer

in_memory_span_exporter = InMemorySpanExporter()


with open(Path(__file__).parent / "test_data" / "mock_responses.json", "r") as f:
    _MOCK_RESPONSES = json.load(f)


@pytest.fixture(autouse=True)
def mock_configure() -> None:
    """Mock Atla configuration to send traces to a local object instead."""
    from atla_insights import configure

    with patch(
        "atla_insights.main.get_atla_span_exporter",
        return_value=in_memory_span_exporter,
    ):
        configure(token="dummy", metadata={"environment": "unit-testing"}, verbose=False)


@pytest.fixture(scope="class")
def mock_openai_client() -> Generator[OpenAI, None, None]:
    """Mock the OpenAI client."""
    with HTTPServer() as httpserver:
        httpserver.expect_request("/v1/chat/completions").respond_with_json(
            _MOCK_RESPONSES["openai_chat_completions"]
        )
        httpserver.expect_request("/v1/responses").respond_with_json(
            _MOCK_RESPONSES["openai_responses"]
        )
        yield OpenAI(api_key="unit-test", base_url=httpserver.url_for("/v1"))


@pytest.fixture(scope="class")
def mock_azure_openai_client() -> Generator[AzureOpenAI, None, None]:
    """Mock the OpenAI client."""
    _AZURE_PREFIX = "/v1/deployments/some-model"
    with HTTPServer() as httpserver:
        httpserver.expect_request(f"{_AZURE_PREFIX}/chat/completions").respond_with_json(
            _MOCK_RESPONSES["openai_chat_completions"]
        )
        httpserver.expect_request(f"{_AZURE_PREFIX}/responses").respond_with_json(
            _MOCK_RESPONSES["openai_responses"]
        )
        yield AzureOpenAI(
            api_key="unit-test",
            base_url=httpserver.url_for("/v1"),
            api_version="2024-02-15-preview",
        )


@pytest.fixture(scope="class")
def mock_async_openai_client() -> Generator[AsyncOpenAI, None, None]:
    """Mock the OpenAI client."""
    with HTTPServer() as httpserver:
        httpserver.expect_request("/v1/chat/completions").respond_with_json(
            _MOCK_RESPONSES["openai_chat_completions"]
        )
        httpserver.expect_request("/v1/responses").respond_with_json(
            _MOCK_RESPONSES["openai_responses"]
        )
        yield AsyncOpenAI(api_key="unit-test", base_url=httpserver.url_for("/v1"))


@pytest.fixture(scope="class")
def mock_async_azure_openai_client() -> Generator[AsyncAzureOpenAI, None, None]:
    """Mock the OpenAI client."""
    _AZURE_PREFIX = "/v1/deployments/some-model"
    with HTTPServer() as httpserver:
        httpserver.expect_request(f"{_AZURE_PREFIX}/chat/completions").respond_with_json(
            _MOCK_RESPONSES["openai_chat_completions"]
        )
        httpserver.expect_request(f"{_AZURE_PREFIX}/responses").respond_with_json(
            _MOCK_RESPONSES["openai_responses"]
        )
        yield AsyncAzureOpenAI(
            api_key="unit-test",
            base_url=httpserver.url_for("/v1"),
            api_version="2024-02-15-preview",
        )


@pytest.fixture(scope="class")
def mock_openai_stream_client() -> Generator[OpenAI, None, None]:
    """Mock the OpenAI client with streaming responses."""
    with HTTPServer() as httpserver:
        # Chat completions streaming
        chat_stream_chunks = _MOCK_RESPONSES["openai_chat_completions_stream"]
        chat_sse_data = (
            "\n\n".join(f"data: {json.dumps(chunk)}" for chunk in chat_stream_chunks)
            + "\n\ndata: [DONE]\n\n"
        )

        httpserver.expect_request("/v1/chat/completions").respond_with_data(
            chat_sse_data, content_type="text/event-stream"
        )

        # Responses API streaming
        responses_stream_chunks = _MOCK_RESPONSES["openai_responses_stream"]
        # Format each event properly with event type and data
        responses_events = []
        for chunk in responses_stream_chunks:
            event_type = chunk.get("type", "message")
            responses_events.append(f"event: {event_type}\ndata: {json.dumps(chunk)}\n")
        responses_sse_data = "\n".join(responses_events) + "\n"

        httpserver.expect_request("/v1/responses").respond_with_data(
            responses_sse_data, content_type="text/event-stream"
        )

        yield OpenAI(api_key="unit-test", base_url=httpserver.url_for("/v1"))


@pytest.fixture(scope="class")
def mock_async_openai_stream_client() -> Generator[AsyncOpenAI, None, None]:
    """Mock the Async OpenAI client with streaming responses."""
    with HTTPServer() as httpserver:
        # Chat completions streaming
        chat_stream_chunks = _MOCK_RESPONSES["openai_chat_completions_stream"]
        chat_sse_data = (
            "\n\n".join(f"data: {json.dumps(chunk)}" for chunk in chat_stream_chunks)
            + "\n\ndata: [DONE]\n\n"
        )

        httpserver.expect_request("/v1/chat/completions").respond_with_data(
            chat_sse_data, content_type="text/event-stream"
        )

        # Responses API streaming
        responses_stream_chunks = _MOCK_RESPONSES["openai_responses_stream"]

        responses_events = []
        for chunk in responses_stream_chunks:
            event_type = chunk.get("type", "message")
            responses_events.append(f"event: {event_type}\ndata: {json.dumps(chunk)}\n")
        responses_sse_data = "\n".join(responses_events) + "\n"

        httpserver.expect_request("/v1/responses").respond_with_data(
            responses_sse_data, content_type="text/event-stream"
        )

        yield AsyncOpenAI(api_key="unit-test", base_url=httpserver.url_for("/v1"))


@pytest.fixture(scope="class")
def mock_failing_openai_client() -> Generator[OpenAI, None, None]:
    """Mock a failing OpenAI client."""
    with HTTPServer() as httpserver:
        mock_response = {
            "error": {
                "message": "Invalid value for 'model': 'gpt-unknown'.",
                "type": "invalid_request_error",
                "param": "model",
                "code": None,
            }
        }
        httpserver.expect_request("/v1/chat/completions").respond_with_json(mock_response)
        httpserver.expect_request("/v1/responses").respond_with_json(mock_response)
        yield OpenAI(api_key="unit-test", base_url=httpserver.url_for("/v1"))


@pytest.fixture(scope="class")
def mock_anthropic_client() -> Generator[Anthropic, None, None]:
    """Mock the Anthropic client."""
    with HTTPServer() as httpserver:
        httpserver.expect_request("/v1/messages").respond_with_json(
            _MOCK_RESPONSES["anthropic_messages"]
        )
        yield Anthropic(api_key="unit-test", base_url=httpserver.url_for(""))


@pytest.fixture(scope="class")
def mock_anthropic_stream_client() -> Generator[Anthropic, None, None]:
    """Mock the Anthropic client with streaming responses."""
    with HTTPServer() as httpserver:
        stream_events = _MOCK_RESPONSES["anthropic_messages_stream"]

        # Anthropic uses SSE format with event: and data: lines
        sse_lines = []
        for event in stream_events:
            event_type = event.get("type", "message")
            sse_lines.append(f"event: {event_type}")
            sse_lines.append(f"data: {json.dumps(event)}")
            sse_lines.append("")
        sse_data = "\n".join(sse_lines) + "\n"

        httpserver.expect_request("/v1/messages").respond_with_data(
            sse_data, content_type="text/event-stream"
        )
        yield Anthropic(api_key="unit-test", base_url=httpserver.url_for(""))


@pytest.fixture(scope="class")
def mock_async_anthropic_client() -> Generator[AsyncAnthropic, None, None]:
    """Mock the Async Anthropic client."""
    with HTTPServer() as httpserver:
        httpserver.expect_request("/v1/messages").respond_with_json(
            _MOCK_RESPONSES["anthropic_messages"]
        )
        yield AsyncAnthropic(api_key="unit-test", base_url=httpserver.url_for(""))


@pytest.fixture(scope="class")
def mock_async_anthropic_stream_client() -> Generator[AsyncAnthropic, None, None]:
    """Mock the Async Anthropic client with streaming responses."""
    with HTTPServer() as httpserver:
        stream_events = _MOCK_RESPONSES["anthropic_messages_stream"]

        # Anthropic uses SSE format with event: and data: lines
        sse_lines = []
        for event in stream_events:
            event_type = event.get("type", "message")
            sse_lines.append(f"event: {event_type}")
            sse_lines.append(f"data: {json.dumps(event)}")
            sse_lines.append("")
        sse_data = "\n".join(sse_lines) + "\n"

        httpserver.expect_request("/v1/messages").respond_with_data(
            sse_data, content_type="text/event-stream"
        )

        yield AsyncAnthropic(api_key="unit-test", base_url=httpserver.url_for(""))


@pytest.fixture(scope="class")
def mock_anthropic_bedrock_client() -> Generator[AnthropicBedrock, None, None]:
    """Mock the Anthropic Bedrock client."""
    with HTTPServer() as httpserver:
        httpserver.expect_request("/model/some-model/invoke").respond_with_json(
            _MOCK_RESPONSES["anthropic_bedrock_messages"]
        )
        yield AnthropicBedrock(
            base_url=httpserver.url_for(""),
            aws_access_key="mock-access-key",
            aws_secret_key="mock-secret-key",
        )


@pytest.fixture(scope="class")
def mock_async_anthropic_bedrock_client() -> Generator[AsyncAnthropicBedrock, None, None]:
    """Mock the Async Anthropic Bedrock client."""
    with HTTPServer() as httpserver:
        httpserver.expect_request("/model/some-model/invoke").respond_with_json(
            _MOCK_RESPONSES["anthropic_bedrock_messages"]
        )
        yield AsyncAnthropicBedrock(
            base_url=httpserver.url_for(""),
            aws_access_key="mock-access-key",
            aws_secret_key="mock-secret-key",
        )


@pytest.fixture(scope="class")
def mock_google_genai_client() -> Generator[Client, None, None]:
    """Mock the Google GenAI client."""
    with HTTPServer() as httpserver:
        httpserver.expect_request(
            "/v1beta/models/some-model:generateContent"
        ).respond_with_json(_MOCK_RESPONSES["google_genai_content"])
        httpserver.expect_request(
            "/v1beta/models/some-tool-call-model:generateContent"
        ).respond_with_json(_MOCK_RESPONSES["google_genai_tool_calls"])

        yield Client(
            api_key="unit-test",
            http_options=HttpOptions(base_url=httpserver.url_for("")),
        )


@pytest.fixture(scope="class")
def mock_google_genai_stream_client() -> Generator[Client, None, None]:
    """Mock the Google GenAI client with streaming responses."""
    with HTTPServer() as httpserver:
        stream_chunks = _MOCK_RESPONSES["google_genai_content_stream"]

        # Google GenAI uses newline-delimited JSON (NDJSON) for streaming
        ndjson_data = "\n".join(json.dumps(chunk) for chunk in stream_chunks) + "\n"

        httpserver.expect_request(
            "/v1beta/models/some-model:streamGenerateContent"
        ).respond_with_data(ndjson_data, content_type="application/json")

        yield Client(
            api_key="unit-test",
            http_options=HttpOptions(base_url=httpserver.url_for("")),
        )


@pytest.fixture(scope="function")
def bedrock_client_factory() -> Generator[
    Callable[[str, dict], Tuple[BaseClient, Stubber]], None, None
]:
    """Factory function to create a stubbed Bedrock client."""

    def _create_client_with_response(model_id: str, response_content: dict):
        client = boto3.client(
            service_name="bedrock-runtime",
            region_name="us-east-1",
        )
        stubber = Stubber(client)
        stubber.activate()

        response_body = json.dumps(response_content).encode()
        mock_response = {
            "body": StreamingBody(io.BytesIO(response_body), len(response_body)),
            "contentType": "application/json",
            "ResponseMetadata": {"HTTPStatusCode": 200},
        }

        stubber.add_response(
            "invoke_model",
            mock_response,
            {
                "body": ANY,
                "modelId": model_id,
            },
        )

        return client, stubber

    clients_and_stubbers: list[Tuple[BaseClient, Stubber]] = []

    def factory(model_id: str, response_content: dict):
        client_stubber = _create_client_with_response(model_id, response_content)
        clients_and_stubbers.append(client_stubber)
        return client_stubber

    yield factory

    # Cleanup all created clients
    for _, stubber in clients_and_stubbers:
        stubber.deactivate()
        stubber.assert_no_pending_responses()


@pytest.fixture(autouse=True)
def mock_claude_code_cli() -> Generator[None, None, None]:
    """Mock the Claude Code CLI."""

    async def mock_recv() -> AsyncGenerator[dict[str, Any], None]:
        responses: list[dict[str, Any]] = [
            {
                "type": "system",
                "subtype": "system",
                "message": {
                    "role": "system",
                    "content": [{"type": "text", "text": "You are a helpful assistant."}],
                },
            },
            {
                "type": "user",
                "message": {
                    "role": "user",
                    "content": [{"type": "text", "text": "foo"}],
                },
            },
            {
                "type": "assistant",
                "message": {
                    "role": "assistant",
                    "model": "some-model",
                    "content": [{"type": "text", "text": "bar"}],
                },
            },
            {
                "type": "result",
                "subtype": "result",
                "duration_ms": 100,
                "duration_api_ms": 100,
                "is_error": False,
                "num_turns": 1,
                "session_id": "default",
                "total_cost_usd": 0.0001,
                "usage": {"prompt_tokens": 100, "completion_tokens": 100},
                "result": "bar",
            },
        ]
        for msg in responses:
            yield msg

    with (
        patch.object(
            claude_code_sdk._internal.transport.subprocess_cli.SubprocessCLITransport,
            "connect",
            return_value=AsyncMock(),
        ),
        patch.object(
            claude_code_sdk._internal.transport.subprocess_cli.SubprocessCLITransport,
            "write",
            return_value=AsyncMock(),
        ),
        patch(
            "claude_code_sdk._internal.transport.subprocess_cli.SubprocessCLITransport._find_cli",
            return_value="foobar",
        ),
        patch.object(
            claude_code_sdk._internal.query.Query,
            "start",
            return_value=AsyncMock(),
        ),
        patch.object(
            claude_code_sdk._internal.query.Query,
            "initialize",
            return_value=AsyncMock(),
        ),
        patch.object(
            claude_code_sdk._internal.query.Query,
            "close",
            return_value=AsyncMock(),
        ),
        patch.object(
            claude_code_sdk._internal.query.Query,
            "receive_messages",
            return_value=mock_recv(),
        ),
    ):
        yield


@pytest.fixture(autouse=True)
def mock_claude_agent_cli() -> Generator[None, None, None]:
    """Mock the Claude Agent CLI."""

    async def mock_recv() -> AsyncGenerator[dict[str, Any], None]:
        responses: list[dict[str, Any]] = [
            {
                "type": "system",
                "subtype": "system",
                "message": {
                    "role": "system",
                    "content": [{"type": "text", "text": "You are a helpful assistant."}],
                },
            },
            {
                "type": "user",
                "message": {
                    "role": "user",
                    "content": [{"type": "text", "text": "foo"}],
                },
            },
            {
                "type": "assistant",
                "message": {
                    "role": "assistant",
                    "model": "some-model",
                    "content": [{"type": "text", "text": "bar"}],
                },
            },
            {
                "type": "result",
                "subtype": "result",
                "duration_ms": 100,
                "duration_api_ms": 100,
                "is_error": False,
                "num_turns": 1,
                "session_id": "default",
                "total_cost_usd": 0.0001,
                "usage": {"prompt_tokens": 100, "completion_tokens": 100},
                "result": "bar",
            },
        ]
        for msg in responses:
            yield msg

    with (
        patch.object(
            claude_agent_sdk._internal.transport.subprocess_cli.SubprocessCLITransport,
            "connect",
            return_value=AsyncMock(),
        ),
        patch.object(
            claude_agent_sdk._internal.transport.subprocess_cli.SubprocessCLITransport,
            "write",
            return_value=AsyncMock(),
        ),
        patch(
            "claude_agent_sdk._internal.transport.subprocess_cli.SubprocessCLITransport._find_cli",
            return_value="foobar",
        ),
        patch.object(
            claude_agent_sdk._internal.query.Query,
            "start",
            return_value=AsyncMock(),
        ),
        patch.object(
            claude_agent_sdk._internal.query.Query,
            "initialize",
            return_value=AsyncMock(),
        ),
        patch.object(
            claude_agent_sdk._internal.query.Query,
            "close",
            return_value=AsyncMock(),
        ),
        patch.object(
            claude_agent_sdk._internal.query.Query,
            "receive_messages",
            return_value=mock_recv(),
        ),
    ):
        yield
