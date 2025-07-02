"""OpenTelemetry samplers for Atla Insights."""

import json
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional, TypedDict, Union

from opentelemetry.context import Context
from opentelemetry.sdk.trace import Span, SpanProcessor, TracerProvider
from opentelemetry.sdk.trace.sampling import (
    ParentBased,
    ParentBasedTraceIdRatio,
    Sampler,
    StaticSampler,
)

from atla_insights.constants import SAMPLING_OPTIONS_MARK

logger = logging.getLogger("atla_insights")


TRACE_SAMPLER_TYPE = Union[ParentBased, StaticSampler]


class _HeadSamplingOptions(ABC):
    """Base class for head sampling options."""

    @abstractmethod
    def to_sampler(self) -> TRACE_SAMPLER_TYPE:
        pass


class _TailSamplingOptions(ABC):
    """Base class for tail sampling options."""

    @abstractmethod
    def to_span_processor(self) -> SpanProcessor:
        pass


TRACE_SAMPLING_TYPE = Union[
    TRACE_SAMPLER_TYPE,
    _HeadSamplingOptions,
    _TailSamplingOptions,
]


@dataclass
class TraceRatioSamplingOptions(_HeadSamplingOptions):
    """Options for trace ratio sampling."""

    rate: float

    def to_sampler(self) -> TRACE_SAMPLER_TYPE:
        """Convert the sampling options to a sampler."""
        return ParentBasedTraceIdRatio(self.rate)


class MetadataSamplingOption(TypedDict):
    """Options for metadata sampling."""

    stratify_by: str
    ratios: dict[str, float]


class _MetadataSpanProcessor(SpanProcessor):
    """Span processor that processes metadata."""

    def __init__(self, options: list[MetadataSamplingOption]) -> None:
        self.options = options

    def on_start(self, span: Span, parent_context: Optional[Context]) -> None:
        options_json = json.dumps(self.options)
        span.set_attribute(SAMPLING_OPTIONS_MARK, options_json)

    def on_end(self, span: Span) -> None:
        pass


@dataclass
class MetadataSamplingOptions(_TailSamplingOptions):
    """Options for trace ratio sampling."""

    options: list[MetadataSamplingOption]

    def to_span_processor(self) -> SpanProcessor:
        """Convert the sampling options to a span processor."""
        return _MetadataSpanProcessor(options=self.options)


def add_sampling_to_tracer_provider(
    tracer_provider: TracerProvider,
    sampling: TRACE_SAMPLING_TYPE,
) -> None:
    """Add sampling to a tracer provider."""
    if isinstance(sampling, Sampler):
        if not isinstance(sampling, TRACE_SAMPLER_TYPE):
            logger.warning(
                "Passed a custom sampler that is not `ParentBased` or `StaticSampler`. "
                "This can result in partial traces being sent to Atla Insights and "
                "unexpected behavior! It is strongly recommended to use a `ParentBased` "
                "or `StaticSampler` instead."
            )
        tracer_provider.sampler = sampling
    elif isinstance(sampling, _HeadSamplingOptions):
        sampler = sampling.to_sampler()
        tracer_provider.sampler = sampler
    elif isinstance(sampling, _TailSamplingOptions):
        span_processor = sampling.to_span_processor()
        tracer_provider.add_span_processor(span_processor)
    else:
        logger.warning(f"Unrecognized sampling type: `{type(sampling)}`")
