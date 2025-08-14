"""Type definitions for Atla Insights API responses."""

from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field


class Environment(str, Enum):
    """Trace environment enumeration."""

    PROD = "PROD"
    DEV = "DEV"


class SpanAnnotation(BaseModel):
    """Annotation attached to a span."""

    id: str
    organization_id: str = Field(alias="organizationId")
    span_id: str = Field(alias="spanId")
    failure_mode: str = Field(alias="failureMode")
    atla_critique: str = Field(alias="atlaCritique")

    model_config = ConfigDict(populate_by_name=True)


class TraceViewSpan(BaseModel):
    """Individual span within a trace."""

    id: str
    organization_id: str = Field(alias="organizationId")
    trace_id: str = Field(alias="traceId")
    parent_span_id: Optional[str] = Field(None, alias="parentSpanId")
    span_name: Optional[str] = Field(None, alias="spanName")
    start_timestamp: str = Field(alias="startTimestamp")
    end_timestamp: str = Field(alias="endTimestamp")
    is_exception: Optional[bool] = Field(None, alias="isException")
    otel_events: List[Dict[str, Any]] = Field(default_factory=list, alias="otelEvents")
    annotations: List[SpanAnnotation] = Field(default_factory=list)

    model_config = ConfigDict(populate_by_name=True)


class CustomMetricDefinition(BaseModel):
    """Definition of a custom metric."""

    id: str
    organization_id: str = Field(alias="organizationId")
    name: str
    data_type: str = Field(alias="dataType")  # "BOOLEAN" or "LIKERT_1_TO_5"

    model_config = ConfigDict(populate_by_name=True)


class CustomMetricValue(BaseModel):
    """Custom metric value attached to a trace."""

    id: str
    organization_id: str = Field(alias="organizationId")
    trace_id: str = Field(alias="traceId")
    custom_metric_id: str = Field(alias="customMetricId")
    value: str  # Stored as string in API
    custom_metric: Optional[CustomMetricDefinition] = Field(None, alias="customMetric")

    model_config = ConfigDict(populate_by_name=True)


class TraceView(BaseModel):
    """Full trace view response."""

    id: str
    organization_id: str = Field(alias="organizationId")
    environment: Environment
    is_success: Optional[bool] = Field(None, alias="isSuccess")
    is_completed: bool = Field(alias="isCompleted")
    metadata: Optional[Dict[str, Any]] = None
    step_count: int = Field(alias="stepCount")
    started_at: str = Field(alias="startedAt")
    ended_at: str = Field(alias="endedAt")
    duration_seconds: float = Field(alias="durationSeconds")
    ingested_at: str = Field(alias="ingestedAt")
    spans: Optional[List[TraceViewSpan]] = None
    custom_metric_values: List[CustomMetricValue] = Field(
        default_factory=list, alias="customMetricValues"
    )

    model_config = ConfigDict(populate_by_name=True)


class TraceListResponse(BaseModel):
    """Response for listing traces."""

    traces: List[TraceView]
    total: float
    page: float
    page_size: float = Field(alias="pageSize")

    model_config = ConfigDict(populate_by_name=True)

    @property
    def has_next_page(self) -> bool:
        """Check if there are more pages available."""
        return (self.page + 1) * self.page_size < self.total


class SingleTraceResponse(BaseModel):
    """Response for getting a single trace."""

    trace: TraceView


class BatchTraceResponse(BaseModel):
    """Response for getting multiple traces by IDs."""

    traces: List[TraceView]
