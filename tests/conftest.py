"""Fixtures for the tests."""

import json
from pathlib import Path
from typing import Generator
from unittest.mock import patch

import pytest
from anthropic import Anthropic, AsyncAnthropic
from google.genai import Client
from google.genai.types import HttpOptions
from openai import AsyncOpenAI, OpenAI
from opentelemetry.sdk.trace.export import SimpleSpanProcessor
from opentelemetry.sdk.trace.export.in_memory_span_exporter import InMemorySpanExporter
from pytest_httpserver import HTTPServer

in_memory_span_exporter = InMemorySpanExporter()


with open(Path(__file__).parent / "test_data" / "mock_responses.json", "r") as f:
    _MOCK_RESPONSES = json.load(f)


@pytest.fixture(scope="session", autouse=True)
def mock_configure() -> None:
    """Mock Atla configuration to send traces to a local object instead."""
    from atla_insights import configure

    span_processor = SimpleSpanProcessor(in_memory_span_exporter)

    with patch(
        "atla_insights.span_processors.get_atla_span_processor",
        return_value=span_processor,
    ):
        configure(token="dummy", metadata={"environment": "unit-testing"})


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
def mock_async_anthropic_client() -> Generator[AsyncAnthropic, None, None]:
    """Mock the Async Anthropic client."""
    with HTTPServer() as httpserver:
        httpserver.expect_request("/v1/messages").respond_with_json(
            _MOCK_RESPONSES["anthropic_messages"]
        )
        yield AsyncAnthropic(api_key="unit-test", base_url=httpserver.url_for(""))


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
