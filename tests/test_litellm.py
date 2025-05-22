"""Test the Litellm integration."""

import asyncio
import json
import time

import litellm
import logfire
import pytest
from litellm import acompletion, completion
from litellm.proxy._types import SpanAttributes
from openai import OpenAI
from opentelemetry.sdk.trace.export import SimpleSpanProcessor
from opentelemetry.sdk.trace.export.in_memory_span_exporter import InMemorySpanExporter

from src.atla_insights import instrument_litellm


@pytest.mark.usefixtures("mock_openai_client")
class TestLitellmIntegration:
    """Test the Litellm integration."""

    in_memory_span_exporter: InMemorySpanExporter

    @classmethod
    def setup_class(cls) -> None:
        """Set up an in-memory span exporter to collect traces to a local object."""
        cls.in_memory_span_exporter = InMemorySpanExporter()

        logfire.configure(
            additional_span_processors=[SimpleSpanProcessor(cls.in_memory_span_exporter)],
            send_to_logfire=False,
        )

    def setup_method(self) -> None:
        """Wipe any pre-existing litellm instrumentation."""
        litellm.callbacks = []
        instrument_litellm()

    def teardown_method(self) -> None:
        """Wipe any added traces after each test run."""
        self.in_memory_span_exporter.clear()

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
        completion(
            **completion_kwargs,
            api_base=str(mock_openai_client.base_url),
            api_key="unit-test",
        )

        time.sleep(1)  # litellm otel logging is async which leads to a race condition

        assert len(self.in_memory_span_exporter.get_finished_spans()) == 1
        [litellm_request] = self.in_memory_span_exporter.get_finished_spans()

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
        await acompletion(
            **completion_kwargs,
            api_base=str(mock_openai_client.base_url),
            api_key="unit-test",
        )

        await asyncio.sleep(1)  # litellm otel logging leads to a race condition

        assert len(self.in_memory_span_exporter.get_finished_spans()) == 1
        [litellm_request] = self.in_memory_span_exporter.get_finished_spans()

        assert litellm_request.attributes is not None

        genai_attributes = {
            k.value if isinstance(k, SpanAttributes) else k: v
            for k, v in litellm_request.attributes.items()
            if k.startswith("gen_ai.")
        }

        assert genai_attributes == expected_genai_attributes
