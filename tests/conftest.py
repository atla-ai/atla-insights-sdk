"""Fixtures for the tests."""

from typing import Generator

import pytest
from openai import OpenAI
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
