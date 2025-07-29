"""Context variables for the atla_insights package."""

from contextvars import ContextVar
from typing import TYPE_CHECKING, Optional

from opentelemetry.sdk.trace import Span

if TYPE_CHECKING:
    from atla_insights.custom_metrics import CustomMetric


custom_metrics_var: ContextVar[Optional[dict[str, "CustomMetric"]]] = ContextVar(
    "custom_metrics_var", default=None
)
metadata_var: ContextVar[Optional[dict[str, str]]] = ContextVar(
    "metadata_var", default=None
)
root_span_var: ContextVar[Optional[Span]] = ContextVar("root_span_var", default=None)
