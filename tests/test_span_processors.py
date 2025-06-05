"""Test the span processors."""

import json
from typing import cast

import pytest

from tests._otel import BaseLocalOtel


class TestInstrumentation(BaseLocalOtel):
    """Test the instrumentation."""

    def test_basic_instrumentation(self) -> None:
        """Test that the instrumented function is traced."""
        from src.atla_insights import instrument

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
        from src.atla_insights import instrument

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


class TestSpanProcessors(BaseLocalOtel):
    """Test the span processors."""

    def test_metadata(self) -> None:
        """Test that run metadata is added to the root span correctly."""
        from src.atla_insights import instrument
        from src.atla_insights._constants import METADATA_MARK

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
        from src.atla_insights import instrument
        from src.atla_insights._constants import SUCCESS_MARK

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
        from src.atla_insights import instrument
        from src.atla_insights._constants import SUCCESS_MARK

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
        from src.atla_insights import instrument
        from src.atla_insights._constants import SUCCESS_MARK

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
        from src.atla_insights import instrument, mark_success
        from src.atla_insights._constants import SUCCESS_MARK

        @instrument()
        def test_function():
            mark_success()
            return "test result"

        test_function()

        spans = self.in_memory_span_exporter.get_finished_spans()

        assert len(spans) == 1
        span = spans[0]

        assert span.attributes is not None
        assert span.attributes.get(SUCCESS_MARK) == 1

    def test_manual_marking_nok(self) -> None:
        """Test that the instrumented function with a manual mark is traced."""
        from src.atla_insights import instrument, mark_failure, mark_success

        @instrument()
        def test_function():
            mark_success()
            mark_failure()  # can only call once
            return "test result"

        with pytest.raises(ValueError):
            test_function()

    def test_manual_marking_nested(self) -> None:
        """Test that the nested instrumented function with a manual mark is traced."""
        from src.atla_insights import instrument, mark_success
        from src.atla_insights._constants import SUCCESS_MARK

        @instrument("root_span")
        def test_function():
            @instrument("nested_span")
            def nested_function():
                mark_success()
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
        from src.atla_insights import instrument
        from src.atla_insights._constants import SUCCESS_MARK

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
        from src.atla_insights import instrument, mark_success
        from src.atla_insights._constants import SUCCESS_MARK

        @instrument()
        def test_function_1():
            mark_success()
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
