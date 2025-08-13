"""Test the marking."""

from tests._otel import BaseLocalOtel


class TestMarking(BaseLocalOtel):
    """Test the marking."""

    def test_no_manual_marking(self) -> None:
        """Test that the instrumented function is traced."""
        from atla_insights import instrument
        from atla_insights.constants import SUCCESS_MARK

        @instrument()
        def test_function():
            return "test result"

        test_function()
        spans = self.get_finished_spans()

        assert len(spans) == 1
        [span] = spans

        assert span.attributes is not None
        assert span.attributes.get(SUCCESS_MARK) == -1

    def test_no_manual_marking_nested_1(self) -> None:
        """Test that the instrumented nested function is traced."""
        from atla_insights import instrument
        from atla_insights.constants import SUCCESS_MARK

        @instrument("root_span")
        def test_function():
            @instrument("nested_span")
            def nested_function():
                return "nested result"

            nested_function()
            return "test result"

        test_function()
        spans = self.get_finished_spans()

        assert len(spans) == 2
        root_span, nested_span = spans

        assert root_span.name == "root_span"
        assert root_span.attributes is not None
        assert root_span.attributes.get(SUCCESS_MARK) == -1
        assert nested_span.name == "nested_span"
        assert nested_span.attributes is not None
        assert nested_span.attributes.get(SUCCESS_MARK) is None

    def test_no_manual_marking_nested_2(self) -> None:
        """Test that the instrumented nested function is traced."""
        from atla_insights import instrument
        from atla_insights.constants import SUCCESS_MARK

        @instrument("nested_span")
        def nested_function():
            return "nested result"

        @instrument("root_span")
        def test_function():
            nested_function()
            return "test result"

        test_function()
        spans = self.get_finished_spans()

        assert len(spans) == 2
        root_span, nested_span = spans

        assert root_span.name == "root_span"
        assert root_span.attributes is not None
        assert root_span.attributes.get(SUCCESS_MARK) == -1
        assert nested_span.name == "nested_span"
        assert nested_span.attributes is not None
        assert nested_span.attributes.get(SUCCESS_MARK) is None

    def test_manual_marking(self) -> None:
        """Test that the instrumented function with a manual mark is traced."""
        from atla_insights import instrument, mark_success
        from atla_insights.constants import SUCCESS_MARK

        @instrument()
        def test_function():
            mark_success()
            return "test result"

        test_function()

        spans = self.get_finished_spans()

        assert len(spans) == 1
        [span] = spans

        assert span.attributes is not None
        assert span.attributes.get(SUCCESS_MARK) == 1

    def test_manual_marking_nested(self) -> None:
        """Test that the nested instrumented function with a manual mark is traced."""
        from atla_insights import instrument, mark_success
        from atla_insights.constants import SUCCESS_MARK

        @instrument("root_span")
        def test_function():
            @instrument("nested_span")
            def nested_function():
                mark_success()
                return "nested result"

            nested_function()
            return "test result"

        test_function()

        spans = self.get_finished_spans()

        assert len(spans) == 2
        root_span, nested_span = spans

        assert root_span.name == "root_span"
        assert root_span.attributes is not None
        assert root_span.attributes.get(SUCCESS_MARK) == 1
        assert nested_span.name == "nested_span"
        assert nested_span.attributes is not None
        assert nested_span.attributes.get(SUCCESS_MARK) is None

    def test_multi_trace_manual_mark(self) -> None:
        """Test that multiple traces with a manual mark are traced."""
        from atla_insights import instrument, mark_success
        from atla_insights.constants import SUCCESS_MARK

        @instrument()
        def test_function_1():
            mark_success()
            return "test result 1"

        test_function_1()

        @instrument()
        def test_function_2():
            return "test result 2"

        test_function_2()

        spans = self.get_finished_spans()

        assert len(spans) == 2
        span_1, span_2 = spans

        assert span_1.attributes is not None
        assert span_1.attributes.get(SUCCESS_MARK) == 1
        assert span_2.attributes is not None
        assert span_2.attributes.get(SUCCESS_MARK) == -1
