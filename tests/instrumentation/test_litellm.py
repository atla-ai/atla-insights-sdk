"""Test the Litellm instrumentation."""

import asyncio
import json
import time

import pytest
from litellm import acompletion, completion
from litellm.proxy._types import SpanAttributes
from openai import OpenAI

from tests._otel import BaseLocalOtel


@pytest.mark.usefixtures("mock_openai_client")
class TestLitellmInstrumentation(BaseLocalOtel):
    """Test the Litellm instrumentation."""

    def test_basic(self) -> None:
        """Test that the Litellm instrumentation is traced."""
        from src.atla_insights import instrument_litellm
        from src.atla_insights._constants import SUCCESS_MARK

        with instrument_litellm():
            completion(
                model="openai/gpt-3.5-turbo",
                messages=[{"role": "user", "content": "hello world"}],
                mock_response="hello world",
            )

        time.sleep(1)  # litellm otel logging is async which leads to a race condition

        spans = self.in_memory_span_exporter.get_finished_spans()

        assert len(spans) == 1
        [litellm_request] = spans

        assert litellm_request.attributes is not None
        assert litellm_request.attributes.get("logfire.msg") == "litellm_request"
        assert litellm_request.attributes.get(SUCCESS_MARK) == -1

    @pytest.mark.asyncio
    async def test_basic_async(self) -> None:
        """Test that the Litellm instrumentation is traced."""
        from src.atla_insights import instrument_litellm
        from src.atla_insights._constants import SUCCESS_MARK

        with instrument_litellm():
            await acompletion(
                model="openai/gpt-3.5-turbo",
                messages=[{"role": "user", "content": "hello world"}],
                mock_response="hello world",
            )

        await asyncio.sleep(1)  # litellm otel logging leads to a race condition

        spans = self.in_memory_span_exporter.get_finished_spans()

        assert len(spans) == 1
        [litellm_request] = spans

        assert litellm_request.attributes is not None
        assert litellm_request.attributes.get("logfire.msg") == "litellm_request"
        assert litellm_request.attributes.get(SUCCESS_MARK) == -1

    @pytest.mark.parametrize(
        "completion_kwargs, expected_genai_attributes",
        [
            pytest.param(
                test_case["completion_kwargs"],
                test_case["expected_genai_attributes"],
                id=test_case["name"],
            )
            for test_case in json.load(open("tests/test_data/litellm_traces.json"))
        ],
    )
    def test_litellm(
        self,
        completion_kwargs: dict,
        expected_genai_attributes: dict,
        mock_openai_client: OpenAI,
    ) -> None:
        """Test the Litellm integration."""
        from src.atla_insights import instrument_litellm

        with instrument_litellm():
            completion(
                **completion_kwargs,
                api_base=str(mock_openai_client.base_url),
                api_key="unit-test",
            )

        time.sleep(1)  # litellm otel logging is async which leads to a race condition

        finished_spans = self.get_finished_spans()

        assert len(finished_spans) == 1
        [litellm_request] = finished_spans

        assert litellm_request.attributes is not None

        genai_attributes = {
            k.value if isinstance(k, SpanAttributes) else k: v
            for k, v in litellm_request.attributes.items()
            if k.startswith("gen_ai.")
        }

        assert genai_attributes == expected_genai_attributes

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "completion_kwargs, expected_genai_attributes",
        [
            pytest.param(
                test_case["completion_kwargs"],
                test_case["expected_genai_attributes"],
                id=test_case["name"],
            )
            for test_case in json.load(open("tests/test_data/litellm_traces.json"))
        ],
    )
    async def test_litellm_async(
        self,
        completion_kwargs: dict,
        expected_genai_attributes: dict,
        mock_openai_client: OpenAI,
    ) -> None:
        """Test the Litellm integration."""
        from src.atla_insights import instrument_litellm

        with instrument_litellm():
            await acompletion(
                **completion_kwargs,
                api_base=str(mock_openai_client.base_url),
                api_key="unit-test",
            )

        await asyncio.sleep(1)  # litellm otel logging leads to a race condition

        finished_spans = self.get_finished_spans()

        assert len(finished_spans) == 1
        [litellm_request] = finished_spans

        assert litellm_request.attributes is not None

        genai_attributes = {
            k.value if isinstance(k, SpanAttributes) else k: v
            for k, v in litellm_request.attributes.items()
            if k.startswith("gen_ai.")
        }

        assert genai_attributes == expected_genai_attributes
