"""Fixtures for the tests."""

from typing import Generator

import pytest
from openai import AsyncOpenAI, OpenAI
from pytest_httpserver import HTTPServer


@pytest.fixture(scope="class")
def mock_openai_client() -> Generator[OpenAI, None, None]:
    """Mock the OpenAI client."""
    with HTTPServer() as httpserver:
        mock_response = {
            "id": "chatcmpl-abc123",
            "object": "chat.completion",
            "created": 1677858242,
            "model": "some-model",
            "choices": [
                {
                    "index": 0,
                    "message": {"role": "assistant", "content": "hello world"},
                    "finish_reason": "stop",
                }
            ],
            "usage": {"prompt_tokens": 9, "completion_tokens": 12, "total_tokens": 21},
        }
        httpserver.expect_request("/v1/chat/completions").respond_with_json(mock_response)
        yield OpenAI(api_key="unit-test", base_url=httpserver.url_for("/v1"))


@pytest.fixture(scope="class")
def mock_async_openai_client() -> Generator[AsyncOpenAI, None, None]:
    """Mock the OpenAI client."""
    with HTTPServer() as httpserver:
        mock_response = {
            "id": "resp_abc123",
            "object": "response",
            "created_at": 1677858242,
            "status": "completed",
            "error": None,
            "incomplete_details": None,
            "instructions": None,
            "max_output_tokens": None,
            "model": "some-model",
            "output": [
                {
                    "type": "message",
                    "id": "msg_abc123",
                    "status": "completed",
                    "role": "assistant",
                    "content": [
                        {"type": "output_text", "text": "hello world", "annotations": []}
                    ],
                }
            ],
        }
        httpserver.expect_request("/v1/responses").respond_with_json(mock_response)
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
        yield OpenAI(api_key="unit-test", base_url=httpserver.url_for("/v1"))
