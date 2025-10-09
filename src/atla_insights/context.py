"""Context variables for the atla_insights package."""

from contextvars import ContextVar
from typing import TYPE_CHECKING, Optional

from opentelemetry.sdk.trace import Span

if TYPE_CHECKING:
    from atla_insights.experiments import Experiment

metadata_var: ContextVar[Optional[dict[str, str]]] = ContextVar(
    "metadata_var", default=None
)
root_span_var: ContextVar[Optional[Span]] = ContextVar("root_span_var", default=None)
suppress_instrumentation_var: ContextVar[bool] = ContextVar(
    "suppress_instrumentation", default=False
)
experiment_var: ContextVar[Optional["Experiment"]] = ContextVar(
    "experiment_var", default=None
)
