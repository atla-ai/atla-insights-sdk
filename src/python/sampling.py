"""OpenTelemetry samplers for Atla Insights."""

import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Union, get_args

from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.sampling import (
    ParentBased,
    ParentBasedTraceIdRatio,
    Sampler,
    StaticSampler,
)

logger = logging.getLogger("atla_insights")


TRACE_SAMPLER_TYPE = Union[ParentBased, StaticSampler]


class _HeadSamplingOptions(ABC):
    """Base class for head sampling options."""

    @abstractmethod
    def to_sampler(self) -> TRACE_SAMPLER_TYPE:
        pass


TRACE_SAMPLING_TYPE = Union[TRACE_SAMPLER_TYPE, _HeadSamplingOptions]


@dataclass
class TraceRatioSamplingOptions(_HeadSamplingOptions):
    """Options for trace ratio sampling."""

    rate: float

    def to_sampler(self) -> TRACE_SAMPLER_TYPE:
        """Convert the sampling options to a sampler."""
        return ParentBasedTraceIdRatio(self.rate)


def add_sampling_to_tracer_provider(
    tracer_provider: TracerProvider,
    sampling: TRACE_SAMPLING_TYPE,
) -> None:
    """Add sampling to a tracer provider."""
    if isinstance(sampling, Sampler):
        if not isinstance(sampling, get_args(TRACE_SAMPLER_TYPE)):
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
    else:
        logger.warning(f"Unrecognized sampling type: `{type(sampling)}`")
