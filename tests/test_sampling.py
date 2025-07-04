"""Test sampling."""

from contextlib import contextmanager
from typing import Generator, Optional, Sequence

from opentelemetry.context import Context
from opentelemetry.sdk.trace.sampling import (
    Decision,
    ParentBased,
    Sampler,
    SamplingResult,
)
from opentelemetry.trace import (
    Link,
    SpanKind,
    TraceState,
)
from opentelemetry.util.types import Attributes

from tests._otel import BaseLocalOtel


@contextmanager
def set_custom_sampler(sampler: Sampler) -> Generator:
    """Set a custom OTEL sampler for the duration of the context.

    :param sampler (Sampler): The sampler to set.
    :return (Generator): A context manager that sets the sampler.
    """
    from atla_insights.main import ATLA_INSTANCE

    assert ATLA_INSTANCE.tracer_provider is not None

    original_sampler = ATLA_INSTANCE.tracer_provider.sampler

    ATLA_INSTANCE.tracer_provider.sampler = sampler
    ATLA_INSTANCE.tracer = ATLA_INSTANCE.get_tracer()

    yield

    ATLA_INSTANCE.tracer_provider.sampler = original_sampler
    ATLA_INSTANCE.tracer = ATLA_INSTANCE.get_tracer()


class TestSampling(BaseLocalOtel):
    """Test sampling."""

    def test_trace_ratio_sampling(self) -> None:
        """Test trace ratio sampling."""
        from atla_insights import instrument
        from atla_insights.sampling import TraceRatioSamplingOptions

        sampler = TraceRatioSamplingOptions(rate=1e-9).to_sampler()

        with set_custom_sampler(sampler):

            @instrument("some_func")
            def test_function():
                return "test result"

            N_ITERATIONS = 100
            for _ in range(N_ITERATIONS):
                test_function()

            spans = self.get_finished_spans()

        assert len(spans) < N_ITERATIONS

    def test_always_on_sampler(self) -> None:
        """Test always on sampler."""
        from opentelemetry.sdk.trace.sampling import ALWAYS_ON

        from atla_insights import instrument

        with set_custom_sampler(ALWAYS_ON):

            @instrument("some_func")
            def test_function():
                return "test result"

            test_function()

            spans = self.get_finished_spans()

        assert len(spans) == 1

    def test_always_off_sampler(self) -> None:
        """Test always off sampler."""
        from opentelemetry.sdk.trace.sampling import ALWAYS_OFF

        from atla_insights import instrument

        with set_custom_sampler(ALWAYS_OFF):

            @instrument("some_func")
            def test_function():
                return "test result"

            test_function()

            spans = self.get_finished_spans()

        assert len(spans) == 0

    def test_custom_sampler(self) -> None:
        """Test custom sampler."""
        from atla_insights import instrument

        class CustomSampler(Sampler):
            """Custom sampler that always records and samples."""

            def get_description(self) -> str:
                return "Custom sampler that always records and samples."

            def should_sample(
                self,
                parent_context: Optional[Context],
                trace_id: int,
                name: str,
                kind: Optional[SpanKind] = None,
                attributes: Attributes = None,
                links: Optional[Sequence[Link]] = None,
                trace_state: Optional[TraceState] = None,
            ) -> SamplingResult:
                return SamplingResult(decision=Decision.RECORD_AND_SAMPLE)

        sampler = ParentBased(root=CustomSampler())

        with set_custom_sampler(sampler):

            @instrument("some_func")
            def test_function():
                return "test result"

            test_function()

            spans = self.get_finished_spans()

        assert len(spans) == 1
