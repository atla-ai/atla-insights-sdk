"""Test the OpenAI instrumentation."""

import json
from typing import cast

import pytest
from openai import OpenAI

from tests._otel import BaseLocalOtel


@pytest.mark.usefixtures("mock_openai_client", "mock_failing_openai_client")
class TestOpenAIInstrumentation(BaseLocalOtel):
    """Test the OpenAI instrumentation."""

    def test_basic(self, mock_openai_client: OpenAI) -> None:
        """Test that the OpenAI instrumentation is traced."""
        from src.atla_insights import instrument_openai
        from src.atla_insights._constants import SUCCESS_MARK

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
        from src.atla_insights import instrument, instrument_openai
        from src.atla_insights._constants import SUCCESS_MARK

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
        from src.atla_insights import instrument, instrument_openai, mark_success
        from src.atla_insights._constants import SUCCESS_MARK

        @instrument("root_span")
        def test_function():
            with instrument_openai(mock_openai_client):
                mock_openai_client.chat.completions.create(
                    model="some-model",
                    messages=[{"role": "user", "content": "hello world"}],
                )

            mark_success()

            return "test result"

        test_function()

        spans = self.in_memory_span_exporter.get_finished_spans()

        assert len(spans) == 2
        _, root_span = spans

        assert root_span.attributes is not None
        assert root_span.attributes.get(SUCCESS_MARK) == 1

    def test_failing_instrumentation(self, mock_failing_openai_client: OpenAI) -> None:
        """Test that the OpenAI instrumentation is traced."""
        from src.atla_insights import instrument_openai
        from src.atla_insights._constants import SUCCESS_MARK

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
        from src.atla_insights import instrument, instrument_openai, mark_success
        from src.atla_insights._constants import SUCCESS_MARK

        @instrument("root_span")
        def test_function():
            with instrument_openai(mock_failing_openai_client):
                mock_failing_openai_client.chat.completions.create(
                    model="some-model",
                    messages=[{"role": "user", "content": "hello world"}],
                )

            mark_success()

            return "test result"

        test_function()

        spans = self.in_memory_span_exporter.get_finished_spans()

        assert len(spans) == 2
        _, root_span = spans

        assert root_span.attributes is not None
        assert root_span.attributes.get(SUCCESS_MARK) == 1

    def test_instrumentation_with_id(self, mock_openai_client: OpenAI) -> None:
        """Test that the OpenAI instrumentation is traced."""
        from src.atla_insights import instrument_openai

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
        from src.atla_insights import instrument_openai

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
