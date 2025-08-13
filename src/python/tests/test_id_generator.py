"""Test custom ID generator."""

import random

from tests._otel import BaseLocalOtel


class TestIdGenerator(BaseLocalOtel):
    """Test custom ID generator."""

    def test_instrumentation_id_conflicts(self) -> None:
        """Test that the id conflicts are handled correctly."""
        from atla_insights import instrument

        _SEED = 10
        random.seed(_SEED)

        @instrument("some_func")
        def test_function():
            return "test result"

        test_function()

        random.seed(_SEED)

        test_function()

        spans = self.get_finished_spans()

        assert len(spans) == 2
        [span_1, span_2] = spans

        context_1 = span_1.get_span_context()
        context_2 = span_2.get_span_context()

        assert context_1 is not None
        assert context_2 is not None

        assert context_1.trace_id != context_2.trace_id
        assert context_1.span_id != context_2.span_id
