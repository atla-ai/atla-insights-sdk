"""OpenTelemetry assets to be used in instrumentation tests."""

import time

import litellm
from opentelemetry.sdk.trace import ReadableSpan

from tests.conftest import in_memory_span_exporter


class BaseLocalOtel:
    """Base class for local OpenTelemetry tests."""

    def teardown_method(self) -> None:
        """Wipe any leftover instrumentation after each test run."""
        in_memory_span_exporter.clear()
        litellm.callbacks = []

    def get_finished_spans(self) -> list[ReadableSpan]:
        """Gets all finished spans from the in-memory span exporter, sorted by time.

        :return (list[ReadableSpan]): The finished spans.
        """
        time.sleep(0.001)  # wait for spans to get collected
        return sorted(
            in_memory_span_exporter.get_finished_spans(),
            key=lambda x: x.start_time if x.start_time is not None else 0,
        )
