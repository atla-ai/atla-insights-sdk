"""Test the span processors."""

import asyncio
import json
import time
from typing import cast

import litellm
import logfire
import pytest
from litellm import acompletion, completion
from openai import OpenAI
from opentelemetry.sdk.trace.export import SimpleSpanProcessor
from opentelemetry.sdk.trace.export.in_memory_span_exporter import InMemorySpanExporter

from src.atla_insights import instrument, instrument_litellm, instrument_openai
from src.atla_insights._constants import METADATA_MARK, SUCCESS_MARK
from src.atla_insights._span_processors import (
    AtlaRootSpanProcessor,
    get_atla_root_span_processor,
)


class TestInstrumentation:
    """Test the instrumentation."""

    in_memory_span_exporter: InMemorySpanExporter

    @classmethod
    def setup_class(cls) -> None:
        """Set up an in-memory span exporter to collect traces to a local object."""
        cls.in_memory_span_exporter = InMemorySpanExporter()

        logfire.configure(
            additional_span_processors=[SimpleSpanProcessor(cls.in_memory_span_exporter)],
            send_to_logfire=False,
        )

    def teardown_method(self) -> None:
        """Wipe any added traces after each test run."""
        self.in_memory_span_exporter.clear()

    def test_basic_instrumentation(self) -> None:
        """Test that the instrumented function is traced."""

        @instrument("some_func")
        def test_function():
            return "test result"

        test_function()
        spans = self.in_memory_span_exporter.get_finished_spans()

        assert len(spans) == 1
        span = spans[0]

        assert span.name == "some_func"

    def test_basic_instrumentation_fail(self) -> None:
        """Test that a failing instrumented function is traced."""

        @instrument("some_failing_func")
        def test_function():
            raise ValueError("test error")

        try:
            test_function()
        except ValueError:
            pass

        spans = self.in_memory_span_exporter.get_finished_spans()

        assert len(spans) == 1
        span = spans[0]

        assert span.name == "some_failing_func"


class BaseSpanProcessors:
    """Base class for span processors tests."""

    atla_root_span_processor: AtlaRootSpanProcessor
    in_memory_span_exporter: InMemorySpanExporter

    @classmethod
    def setup_class(cls) -> None:
        """Set up an in-memory span exporter to collect traces to a local object."""
        cls.atla_root_span_processor = get_atla_root_span_processor(
            metadata={"environment": "unit-testing"},
        )
        cls.in_memory_span_exporter = InMemorySpanExporter()

        logfire.configure(
            additional_span_processors=[
                cls.atla_root_span_processor,
                SimpleSpanProcessor(cls.in_memory_span_exporter),
            ],
            send_to_logfire=False,
        )

    def teardown_method(self) -> None:
        """Wipe any added traces after each test run."""
        self.in_memory_span_exporter.clear()


class TestSpanProcessors(BaseSpanProcessors):
    """Test the span processors."""

    def test_metadata(self) -> None:
        """Test that run metadata is added to the root span correctly."""

        @instrument()
        def test_function():
            return "test result"

        test_function()
        spans = self.in_memory_span_exporter.get_finished_spans()

        assert len(spans) == 1
        span = spans[0]

        assert span.attributes is not None
        assert span.attributes.get(METADATA_MARK) is not None

        metadata = json.loads(cast(str, span.attributes.get(METADATA_MARK)))
        assert metadata == {"environment": "unit-testing"}

    def test_no_manual_marking(self) -> None:
        """Test that the instrumented function is traced."""

        @instrument()
        def test_function():
            return "test result"

        test_function()
        spans = self.in_memory_span_exporter.get_finished_spans()

        assert len(spans) == 1
        span = spans[0]

        assert span.attributes is not None
        assert span.attributes.get(SUCCESS_MARK) == -1

    def test_no_manual_marking_nested_1(self) -> None:
        """Test that the instrumented nested function is traced."""

        @instrument("root_span")
        def test_function():
            @instrument("nested_span")
            def nested_function():
                return "nested result"

            nested_function()
            return "test result"

        test_function()
        spans = self.in_memory_span_exporter.get_finished_spans()

        assert len(spans) == 2
        nested_span, root_span = spans

        assert root_span.name == "root_span"
        assert root_span.attributes is not None
        assert root_span.attributes.get(SUCCESS_MARK) == -1
        assert nested_span.name == "nested_span"
        assert nested_span.attributes is not None
        assert nested_span.attributes.get(SUCCESS_MARK) is None

    def test_no_manual_marking_nested_2(self) -> None:
        """Test that the instrumented nested function is traced."""

        @instrument("nested_span")
        def nested_function():
            return "nested result"

        @instrument("root_span")
        def test_function():
            nested_function()
            return "test result"

        test_function()
        spans = self.in_memory_span_exporter.get_finished_spans()

        assert len(spans) == 2
        nested_span, root_span = spans

        assert root_span.name == "root_span"
        assert root_span.attributes is not None
        assert root_span.attributes.get(SUCCESS_MARK) == -1
        assert nested_span.name == "nested_span"
        assert nested_span.attributes is not None
        assert nested_span.attributes.get(SUCCESS_MARK) is None

    def test_manual_marking(self) -> None:
        """Test that the instrumented function with a manual mark is traced."""

        @instrument()
        def test_function():
            self.atla_root_span_processor.mark_root(value=1)
            return "test result"

        test_function()

        spans = self.in_memory_span_exporter.get_finished_spans()

        assert len(spans) == 1
        span = spans[0]

        assert span.attributes is not None
        assert span.attributes.get(SUCCESS_MARK) == 1

    def test_manual_marking_nok(self) -> None:
        """Test that the instrumented function with a manual mark is traced."""

        @instrument()
        def test_function():
            self.atla_root_span_processor.mark_root(value=1)
            self.atla_root_span_processor.mark_root(value=0)  # can only call once
            return "test result"

        with pytest.raises(ValueError):
            test_function()

    def test_manual_marking_nested(self) -> None:
        """Test that the nested instrumented function with a manual mark is traced."""

        @instrument("root_span")
        def test_function():
            @instrument("nested_span")
            def nested_function():
                self.atla_root_span_processor.mark_root(value=1)
                return "nested result"

            nested_function()
            return "test result"

        test_function()

        spans = self.in_memory_span_exporter.get_finished_spans()

        assert len(spans) == 2
        nested_span, root_span = spans

        assert root_span.name == "root_span"
        assert root_span.attributes is not None
        assert root_span.attributes.get(SUCCESS_MARK) == 1
        assert nested_span.name == "nested_span"
        assert nested_span.attributes is not None
        assert nested_span.attributes.get(SUCCESS_MARK) is None

    def test_multi_trace(self) -> None:
        """Test that multiple traces are traced."""

        @instrument()
        def test_function_1():
            return "test result 1"

        @instrument()
        def test_function_2():
            return "test result 2"

        test_function_1()
        test_function_2()

        spans = self.in_memory_span_exporter.get_finished_spans()

        assert len(spans) == 2
        span_1, span_2 = spans

        assert span_1.attributes is not None
        assert span_1.attributes.get(SUCCESS_MARK) == -1
        assert span_2.attributes is not None
        assert span_2.attributes.get(SUCCESS_MARK) == -1

    def test_multi_trace_manual_mark(self) -> None:
        """Test that multiple traces with a manual mark are traced."""

        @instrument()
        def test_function_1():
            self.atla_root_span_processor.mark_root(value=1)
            return "test result 1"

        test_function_1()

        @instrument()
        def test_function_2():
            return "test result 2"

        test_function_2()

        spans = self.in_memory_span_exporter.get_finished_spans()

        assert len(spans) == 2
        span_1, span_2 = spans

        assert span_1.attributes is not None
        assert span_1.attributes.get(SUCCESS_MARK) == 1
        assert span_2.attributes is not None
        assert span_2.attributes.get(SUCCESS_MARK) == -1


@pytest.mark.usefixtures("mock_openai_client", "mock_failing_openai_client")
class TestOpenAIInstrumentation(BaseSpanProcessors):
    """Test the OpenAI instrumentation."""

    def test_basic_instrumentation(self, mock_openai_client: OpenAI) -> None:
        """Test that the OpenAI instrumentation is traced."""
        with instrument_openai(mock_openai_client):
            mock_openai_client.chat.completions.create(
                model="some-model",
                messages=[{"role": "user", "content": "hello world"}],
            )

        spans = self.in_memory_span_exporter.get_finished_spans()

        assert len(spans) == 1
        span = spans[0]

        assert span.attributes is not None

        request_data = cast(str, span.attributes.get("request_data"))
        assert json.loads(request_data) == {
            "model": "some-model",
            "messages": [{"role": "user", "content": "hello world"}],
        }

        assert span.attributes.get("response_data") is not None

        assert span.attributes.get(SUCCESS_MARK) == -1

    def test_nested_instrumentation(self, mock_openai_client: OpenAI) -> None:
        """Test that the OpenAI instrumentation is traced."""

        @instrument("root_span")
        def test_function():
            with instrument_openai(mock_openai_client):
                mock_openai_client.chat.completions.create(
                    model="some-model",
                    messages=[{"role": "user", "content": "hello world"}],
                )

            return "test result"

        test_function()

        spans = self.in_memory_span_exporter.get_finished_spans()

        assert len(spans) == 2
        generation_span, root_span = spans

        assert root_span.name == "root_span"
        assert root_span.attributes is not None
        assert root_span.attributes.get(SUCCESS_MARK) == -1

        assert generation_span.attributes is not None
        assert generation_span.attributes.get("request_data") is not None
        assert generation_span.attributes.get("response_data") is not None
        assert generation_span.attributes.get(SUCCESS_MARK) is None

    def test_nested_instrumentation_marked(self, mock_openai_client: OpenAI) -> None:
        """Test that the OpenAI instrumentation is traced."""

        @instrument("root_span")
        def test_function():
            with instrument_openai(mock_openai_client):
                mock_openai_client.chat.completions.create(
                    model="some-model",
                    messages=[{"role": "user", "content": "hello world"}],
                )

            self.atla_root_span_processor.mark_root(value=1)

            return "test result"

        test_function()

        spans = self.in_memory_span_exporter.get_finished_spans()

        assert len(spans) == 2
        _, root_span = spans

        assert root_span.attributes is not None
        assert root_span.attributes.get(SUCCESS_MARK) == 1

    def test_failing_instrumentation(self, mock_failing_openai_client: OpenAI) -> None:
        """Test that the OpenAI instrumentation is traced."""
        with instrument_openai(mock_failing_openai_client):
            mock_failing_openai_client.chat.completions.create(
                model="some-model",
                messages=[{"role": "user", "content": "hello world"}],
            )

        spans = self.in_memory_span_exporter.get_finished_spans()

        assert len(spans) == 1
        span = spans[0]

        assert span.attributes is not None

        request_data = cast(str, span.attributes.get("request_data"))
        assert json.loads(request_data) == {
            "model": "some-model",
            "messages": [{"role": "user", "content": "hello world"}],
        }

        assert span.attributes.get("response_data") is None

        assert span.attributes.get(SUCCESS_MARK) == -1

    def test_failing_instrumentation_marked(
        self, mock_failing_openai_client: OpenAI
    ) -> None:
        """Test that the OpenAI instrumentation is traced."""

        @instrument("root_span")
        def test_function():
            with instrument_openai(mock_failing_openai_client):
                mock_failing_openai_client.chat.completions.create(
                    model="some-model",
                    messages=[{"role": "user", "content": "hello world"}],
                )

            self.atla_root_span_processor.mark_root(value=1)

            return "test result"

        test_function()

        spans = self.in_memory_span_exporter.get_finished_spans()

        assert len(spans) == 2
        _, root_span = spans

        assert root_span.attributes is not None
        assert root_span.attributes.get(SUCCESS_MARK) == 1

    def test_instrumentation_with_id(self, mock_openai_client: OpenAI) -> None:
        """Test that the OpenAI instrumentation is traced."""
        client_id = "my-test-agent"

        with instrument_openai(mock_openai_client, client_id):
            mock_openai_client.chat.completions.create(
                model="some-model",
                messages=[{"role": "user", "content": "hello world"}],
            )

        spans = self.in_memory_span_exporter.get_finished_spans()

        assert len(spans) == 1
        span = spans[0]

        assert span.attributes is not None
        logfire_tags = cast(list, span.attributes.get("logfire.tags"))
        assert client_id in logfire_tags

    def test_instrumentation_multiple_ids(
        self,
        mock_openai_client: OpenAI,
        mock_failing_openai_client: OpenAI,
    ) -> None:
        """Test that the OpenAI instrumentation is traced."""
        client_id = "my-test-agent"
        client_id_2 = "my-other-test-agent"

        instrument_openai(mock_openai_client, client_id)
        instrument_openai(mock_failing_openai_client, client_id_2)

        mock_openai_client.chat.completions.create(
            model="some-model",
            messages=[{"role": "user", "content": "hello world"}],
        )

        mock_failing_openai_client.chat.completions.create(
            model="some-model",
            messages=[{"role": "user", "content": "hello world"}],
        )

        spans = self.in_memory_span_exporter.get_finished_spans()

        assert len(spans) == 2
        span_1, span_2 = spans

        assert span_1.attributes is not None
        logfire_tags_1 = cast(list, span_1.attributes.get("logfire.tags"))
        assert client_id in logfire_tags_1
        assert client_id_2 not in logfire_tags_1

        assert span_2.attributes is not None
        logfire_tags_2 = cast(list, span_2.attributes.get("logfire.tags"))
        assert client_id_2 in logfire_tags_2
        assert client_id not in logfire_tags_2


class TestLitellmInstrumentation(BaseSpanProcessors):
    """Test the Litellm instrumentation."""

    def setup_method(self) -> None:
        """Wipe any pre-existing litellm instrumentation."""
        litellm.callbacks = []

    def test_basic_instrumentation(self) -> None:
        """Test that the Litellm instrumentation is traced."""
        instrument_litellm()

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
    async def test_basic_instrumentation_async(self) -> None:
        """Test that the Litellm instrumentation is traced."""
        instrument_litellm()

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
