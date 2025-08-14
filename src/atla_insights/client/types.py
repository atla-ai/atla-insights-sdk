"""Types for the Atla Insights data API."""

from atla_insights.client._generated_client.models import (
    GetTraceById200Response,
    GetTracesByIds200Response,
    GetTracesByIds200ResponseTracesInner,
    GetTracesByIds200ResponseTracesInnerCustomMetricValuesInner,
    GetTracesByIds200ResponseTracesInnerCustomMetricValuesInnerCustomMetric,
    GetTracesByIds200ResponseTracesInnerSpansInner,
    GetTracesByIds200ResponseTracesInnerSpansInnerAnnotationsInner,
    ListTraces200Response,
    ListTraces200ResponseTracesInner,
    ListTracesMetadataFilterParameterInner,
)

Annotation = GetTracesByIds200ResponseTracesInnerSpansInnerAnnotationsInner
CustomMetric = GetTracesByIds200ResponseTracesInnerCustomMetricValuesInnerCustomMetric
CustomMetricValue = GetTracesByIds200ResponseTracesInnerCustomMetricValuesInner
DetailedTraceListResponse = GetTracesByIds200Response
MetadataFilter = ListTracesMetadataFilterParameterInner
Span = GetTracesByIds200ResponseTracesInnerSpansInner
Trace = ListTraces200ResponseTracesInner
TraceDetailResponse = GetTraceById200Response
TraceListResponse = ListTraces200Response
TraceWithDetails = GetTracesByIds200ResponseTracesInner

# Export all the clean names
__all__ = [
    "Annotation",
    "CustomMetric",
    "CustomMetricValue",
    "DetailedTraceListResponse",
    "MetadataFilter",
    "Span",
    "Trace",
    "TraceDetailResponse",
    "TraceListResponse",
    "TraceWithDetails",
]
