"""Test the Litellm instrumentation."""

import asyncio
import json

import pytest
from litellm import acompletion, completion
from litellm.proxy._types import SpanAttributes
from openai import OpenAI

from tests._otel import BaseLocalOtel


class TestLitellmInstrumentation(BaseLocalOtel):
    """Test the Litellm instrumentation."""

    def test_basic(self) -> None:
        """Test that the Litellm instrumentation is traced."""
        from atla_insights import instrument_litellm
        from atla_insights.constants import SUCCESS_MARK

        with instrument_litellm():
            completion(
                model="openai/gpt-3.5-turbo",
                messages=[{"role": "user", "content": "hello world"}],
                mock_response="hello world",
            )

        spans = self.get_finished_spans()

        assert len(spans) == 1
        [litellm_request] = spans

        assert litellm_request.attributes is not None
        assert litellm_request.attributes.get("atla.instrumentation.name") == "litellm"
        assert litellm_request.attributes.get(SUCCESS_MARK) == -1

    @pytest.mark.asyncio
    async def test_basic_async(self) -> None:
        """Test that the Litellm instrumentation is traced."""
        from atla_insights import instrument_litellm
        from atla_insights.constants import SUCCESS_MARK

        with instrument_litellm():
            await acompletion(
                model="openai/gpt-3.5-turbo",
                messages=[{"role": "user", "content": "hello world"}],
                mock_response="hello world",
            )

        await asyncio.sleep(0.001)  # wait for spans to get collected
        spans = self.get_finished_spans()

        assert len(spans) == 1
        [litellm_request] = spans

        assert litellm_request.attributes is not None
        assert litellm_request.attributes.get("atla.instrumentation.name") == "litellm"
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
        from atla_insights import instrument_litellm

        with instrument_litellm():
            completion(
                **completion_kwargs,
                api_base=str(mock_openai_client.base_url),
                api_key="unit-test",
            )

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
        from atla_insights import instrument_litellm

        with instrument_litellm():
            await acompletion(
                **completion_kwargs,
                api_base=str(mock_openai_client.base_url),
                api_key="unit-test",
            )

        await asyncio.sleep(0.001)  # wait for spans to get collected
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

    def test_ctx(self) -> None:
        """Test that the Litellm instrumentation is traced."""
        from atla_insights import instrument_litellm

        with instrument_litellm():
            completion(
                model="openai/gpt-3.5-turbo",
                messages=[{"role": "user", "content": "hello world"}],
                mock_response="hello world",
            )

        completion(
            model="openai/gpt-3.5-turbo",
            messages=[{"role": "user", "content": "hello world"}],
            mock_response="hello world",
        )

        finished_spans = self.get_finished_spans()

        assert len(finished_spans) == 1

    def test_nesting(self) -> None:
        """Test that the Litellm instrumentation is traced."""
        from atla_insights import instrument, instrument_litellm

        @instrument("my_function")
        def my_function() -> None:
            with instrument_litellm():
                completion(
                    model="openai/gpt-3.5-turbo",
                    messages=[{"role": "user", "content": "hello world"}],
                    mock_response="hello world",
                )

        my_function()

        finished_spans = self.get_finished_spans()

        assert len(finished_spans) == 2

        root_span, request = finished_spans

        assert root_span.name == "my_function"
        assert root_span.context is not None
        assert root_span.parent is None

        assert request.name == "litellm_request"
        assert request.parent is not None
        assert request.parent.span_id == root_span.context.span_id
