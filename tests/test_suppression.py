"""Test the suppression functionality."""

from openai import OpenAI

from tests._otel import BaseLocalOtel
from tests.conftest import in_memory_span_exporter


class TestSuppression(BaseLocalOtel):
    """Test instrumentation suppression."""

    def test_suppress_instrumentation_1(self, mock_openai_client: OpenAI) -> None:
        """Test the suppress_instrumentation function."""
        from atla_insights import (
            instrument,
            instrument_openai,
            suppress_instrumentation,
        )

        @instrument("test_function")
        def test_function() -> None:
            """Test function."""
            mock_openai_client.chat.completions.create(
                model="some-model",
                messages=[{"role": "user", "content": "hello world"}],
            )

        # Check all spans get suppressed
        with instrument_openai():
            with suppress_instrumentation():
                test_function()
            assert len(self.get_finished_spans()) == 0

            # Check all spans get instrumented
            test_function()
            assert len(self.get_finished_spans()) == 2

    def test_suppress_instrumentation_2(self, mock_openai_client: OpenAI) -> None:
        """Test the suppress_instrumentation function."""
        from atla_insights import (
            instrument,
            instrument_openai,
            suppress_instrumentation,
        )

        @instrument("test_function")
        def test_function() -> None:
            """Test function."""
            mock_openai_client.chat.completions.create(
                model="some-model",
                messages=[{"role": "user", "content": "hello world"}],
            )

        # Check all spans get suppressed
        with suppress_instrumentation():
            instrument_openai()  # should be a no-op
            test_function()
        assert len(self.get_finished_spans()) == 0

        # Check all spans get instrumented & instrument_openai is a no-op
        test_function()
        assert len(self.get_finished_spans()) == 1
        in_memory_span_exporter.clear()

        # Check all spans get instrumented & this instrument_openai is not a no-op
        with instrument_openai():
            test_function()
        assert len(self.get_finished_spans()) == 2
