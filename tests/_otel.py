"""OpenTelemetry assets to be used in instrumentation tests."""

import time
from unittest.mock import patch

import litellm
from opentelemetry.sdk.trace import ReadableSpan
from opentelemetry.sdk.trace.export import SimpleSpanProcessor
from opentelemetry.sdk.trace.export.in_memory_span_exporter import InMemorySpanExporter


class BaseLocalOtel:
    """Base class for local OpenTelemetry tests."""

    in_memory_span_exporter: InMemorySpanExporter

    @classmethod
    def setup_class(cls) -> None:
        """Set up an in-memory span exporter to collect traces to a local object."""
        from src.atla_insights import configure

        cls.in_memory_span_exporter = InMemorySpanExporter()
        span_processor = SimpleSpanProcessor(cls.in_memory_span_exporter)

        with patch(
            "src.atla_insights._main.get_atla_span_processor",
            return_value=span_processor,
        ):
            configure(token="dummy", metadata={"environment": "unit-testing"})

    def teardown_method(self) -> None:
        """Wipe any leftover instrumentation after each test run."""
        self.in_memory_span_exporter.clear()

        litellm.callbacks = []

    def get_finished_spans(self) -> list[ReadableSpan]:
        """Gets all finished spans from the in-memory span exporter, sorted by time.

        :return (list[ReadableSpan]): The finished spans.
        """
        time.sleep(0.001)  # wait for spans to get collected
        return sorted(
            self.in_memory_span_exporter.get_finished_spans(),
            key=lambda x: x.start_time if x.start_time is not None else 0,
        )
