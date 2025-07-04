"""Custom OpenTelemetry ID generator."""

import random

from opentelemetry import trace
from opentelemetry.sdk.trace.id_generator import RandomIdGenerator


class NoSeedIdGenerator(RandomIdGenerator):
    """Custom OpenTelemetry ID generator, uninfluenced by any pre-existing random seed."""

    rng = random.Random()

    def generate_span_id(self) -> int:
        """Generate a span ID."""
        span_id = self.rng.getrandbits(64)
        while span_id == trace.INVALID_SPAN_ID:
            span_id = self.rng.getrandbits(64)
        return span_id

    def generate_trace_id(self) -> int:
        """Generate a trace ID."""
        trace_id = self.rng.getrandbits(128)
        while trace_id == trace.INVALID_TRACE_ID:
            trace_id = self.rng.getrandbits(128)
        return trace_id
