"""Context variables for the atla_insights package."""

from contextvars import ContextVar
from typing import Optional

from opentelemetry.sdk.trace import Span

metadata_var: ContextVar[Optional[dict[str, str]]] = ContextVar(
    "metadata_var", default=None
)
root_span_var: ContextVar[Optional[Span]] = ContextVar("root_span_var", default=None)
suppress_instrumentation_var: ContextVar[bool] = ContextVar(
    "suppress_instrumentation", default=False
)
