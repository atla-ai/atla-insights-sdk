"""Types for the Atla Insights data API."""

# Import the cleanly named generated models directly
from atla_insights.client._generated_client.models import (
    Annotation,
    CustomMetric,
    CustomMetricValue,
    DetailedTraceListResponse,
    Span,
    Trace,
    TraceDetailResponse,
    TraceListResponse,
    TraceWithDetails,
)

# Export all the clean names
__all__ = [
    "Annotation",
    "CustomMetric",
    "CustomMetricValue",
    "DetailedTraceListResponse",
    "Span",
    "Trace",
    "TraceDetailResponse",
    "TraceListResponse",
    "TraceWithDetails",
]
