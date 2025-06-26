"""Test the span processors."""

from tests._otel import BaseLocalOtel


class TestSpanProcessors(BaseLocalOtel):
    """Test the span processors."""

    def test_basic_instrumentation(self) -> None:
        """Test that the instrumented function is traced."""
        from atla_insights import instrument

        @instrument("some_func")
        def test_function():
            return "test result"

        test_function()
        spans = self.get_finished_spans()

        assert len(spans) == 1
        [span] = spans

        assert span.name == "some_func"

    def test_basic_instrumentation_fail(self) -> None:
        """Test that a failing instrumented function is traced."""
        from atla_insights import instrument

        @instrument("some_failing_func")
        def test_function():
            raise ValueError("test error")

        try:
            test_function()
        except ValueError:
            pass

        spans = self.get_finished_spans()

        assert len(spans) == 1
        [span] = spans

        assert span.name == "some_failing_func"

    def test_multi_trace(self) -> None:
        """Test that multiple traces are traced."""
        from atla_insights import instrument
        from atla_insights.constants import SUCCESS_MARK

        @instrument()
        def test_function_1():
            return "test result 1"

        @instrument()
        def test_function_2():
            return "test result 2"

        test_function_1()
        test_function_2()

        spans = self.get_finished_spans()

        assert len(spans) == 2
        span_1, span_2 = spans

        assert span_1.attributes is not None
        assert span_1.attributes.get(SUCCESS_MARK) == -1
        assert span_2.attributes is not None
        assert span_2.attributes.get(SUCCESS_MARK) == -1
