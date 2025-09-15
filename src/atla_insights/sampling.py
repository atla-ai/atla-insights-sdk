"""OpenTelemetry samplers for Atla Insights."""

import json
import logging
import threading
import time
from typing import Callable, Optional, Union

from opentelemetry.context import Context
from opentelemetry.sdk.trace import ReadableSpan
from opentelemetry.sdk.trace.export import SpanExporter, SpanProcessor
from opentelemetry.sdk.trace.sampling import (
    ParentBased,
    ParentBasedTraceIdRatio,
    StaticSampler,
)

from atla_insights.constants import METADATA_MARK

logger = logging.getLogger("atla_insights")


# Alias chosen opentelemetry samplers for convenience (Atla is not guaranteed to work
# well with any sampler (particularly non static or parent-based samplers))
TraceRatioSampler = ParentBasedTraceIdRatio


class _TailSampler(SpanProcessor):
    """General tail-based sampler class.

    Buffers spans per trace and makes an export decision once the trace is complete.
    """

    def __init__(
        self,
        decision_fn: Callable[[list[ReadableSpan]], bool],
        linger_ms: int = 5 * 60 * 1000,
        reap_interval_ms: int = 2 * 60 * 1000,
        max_traces: int = 50_000,
        max_spans_per_trace: int = 10_000,
    ) -> None:
        """Initialize the TailSamplingSpanProcessor."""
        self._exporters: list[SpanExporter] = []
        self._decide = decision_fn

        self._linger_ms = linger_ms
        self._reap_interval_ms = reap_interval_ms
        self._max_traces = max_traces
        self._max_spans_per_trace = max_spans_per_trace

        self._traces: dict[int, dict[str, object]] = {}
        self._lock = threading.RLock()
        self._shutdown = False

        self._reaper = threading.Thread(
            target=self._reap_loop, name="atla-tail-sampling-reaper", daemon=True
        )
        self._reaper.start()

    def add_exporter(self, exporter: SpanExporter) -> None:
        """Add an exporter to the TailSampler."""
        self._exporters.append(exporter)

    def on_start(
        self, span: ReadableSpan, parent_context: Optional[Context] = None
    ) -> None:
        """On start span processing.

        :param span (ReadableSpan): The span to process.
        :param parent_context (Optional[Context]): The parent context. Defaults to `None`.
        """
        if self._shutdown:
            return

        trace_id = span.context.trace_id
        now = time.time()
        with self._lock:
            state = self._traces.get(trace_id)
            if state is None:
                if len(self._traces) >= self._max_traces:
                    self._traces.pop(next(iter(self._traces)))
                state = {
                    "spans": [],
                    "open": 0,
                    "root_seen": False,
                    "first_seen": now,
                    "last_update": now,
                }
                self._traces[trace_id] = state
            state["open"] = int(state["open"]) + 1  # type: ignore
            state["last_update"] = now

    def on_end(self, span: ReadableSpan) -> None:
        """On end span processing.

        :param span (ReadableSpan): The span to process.
        """
        if self._shutdown:
            return

        trace_id = span.context.trace_id
        now = time.time()
        with self._lock:
            state = self._traces.get(trace_id)
            if state is None:
                state = {
                    "spans": [],
                    "open": 0,
                    "root_seen": False,
                    "first_seen": now,
                    "last_update": now,
                }
                self._traces[trace_id] = state

            spans_list: list[ReadableSpan] = state["spans"]  # type: ignore

            if len(spans_list) < self._max_spans_per_trace:
                spans_list.append(span)

            state["open"] = max(0, int(state["open"]) - 1)  # type: ignore
            state["last_update"] = now

            if span.parent is None:
                state["root_seen"] = True

            if state["root_seen"] and int(state["open"]) == 0:  # type: ignore
                self._finalize_trace_locked(trace_id)

    def shutdown(self) -> None:
        """Shutdown the TailSampler."""
        with self._lock:
            if self._shutdown:
                return
            self._shutdown = True

        self.force_flush()
        for exporter in self._exporters:
            exporter.shutdown()

    def force_flush(self, timeout_millis: int = 30_000) -> bool:
        """Force flush the TailSampler."""
        deadline = time.time() + timeout_millis / 1000.0

        with self._lock:
            trace_ids = list(self._traces.keys())

        for tid in trace_ids:
            with self._lock:
                if tid in self._traces:
                    self._maybe_finalize_by_time_locked(tid, force=True)

        remaining = max(0, deadline - time.time())
        end = time.time() + remaining
        return time.time() <= end

    def _reap_loop(self) -> None:
        """Reap loop for the TailSampler."""
        while not self._shutdown:
            time.sleep(self._reap_interval_ms / 1000.0)
            now = time.time()
            expired: list[int] = []
            with self._lock:
                for tid, state in list(self._traces.items()):
                    last_update = float(state["last_update"])  # type: ignore
                    if (now - last_update) * 1000.0 >= self._linger_ms:
                        expired.append(tid)
                for tid in expired:
                    if tid in self._traces:
                        self._maybe_finalize_by_time_locked(tid, force=False)

    def _maybe_finalize_by_time_locked(self, trace_id: int, force: bool) -> None:
        """Finalize a trace if linger elapsed and root has ended (or force=True)."""
        state = self._traces.get(trace_id)
        if state is None:
            return

        root_seen = bool(state["root_seen"])
        if force or root_seen:
            self._finalize_trace_locked(trace_id)

    def _finalize_trace_locked(self, trace_id: int) -> None:
        """Finalize a trace if root has ended."""
        state = self._traces.pop(trace_id, None)
        if not state:
            return
        spans_list: list[ReadableSpan] = state["spans"]  # type: ignore

        try:
            export_this_trace = self._decide(spans_list)
        except Exception:
            export_this_trace = False

        if export_this_trace and spans_list:
            for exporter in self._exporters:
                exporter.export(spans_list)


class MetadataSampler(_TailSampler):
    """Sampler based on metadata."""

    def __init__(self, decision_fn: Callable[[Optional[dict[str, str]]], bool]) -> None:
        """Initialize the MetadataSampler."""

        def _decision_fn(spans: list[ReadableSpan]) -> bool:
            """Helper function that extracts metadata from root span and passes it on.

            :param spans (list[ReadableSpan]): The spans to process.
            :return (bool): The decision to export the trace.
            """
            decision = True  # default open
            for span in spans:
                if span.parent is None and span.attributes is not None:
                    metadata = span.attributes.get(METADATA_MARK)
                    decision = decision_fn(
                        json.loads(str(metadata)) if metadata else None
                    )
                    break
            return decision

        super().__init__(_decision_fn)


SamplerType = Union[ParentBased, StaticSampler, _TailSampler]
