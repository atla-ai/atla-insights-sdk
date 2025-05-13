"""LiteLLM integration."""

try:
    from litellm.integrations.custom_logger import CustomLogger
    from litellm.integrations.opentelemetry import OpenTelemetry
except ImportError as e:
    raise ImportError(
        "Litellm needs to be installed in order to use the litellm integration. "
        "Please install it via `pip install litellm`."
    ) from e

from opentelemetry import trace
from opentelemetry.trace import SpanKind


class AtlaLiteLLMOpenTelemetry(OpenTelemetry):
    """An Atla LiteLLM OpenTelemetry integration."""

    def __init__(self, **kwargs) -> None:
        """Initialize the Atla LiteLLM OpenTelemetry integration."""
        self.config = {}
        self.tracer = trace.get_tracer("logfire")
        self.callback_name = None
        self.span_kind = SpanKind

        CustomLogger.__init__(self, **kwargs)
        self._init_otel_logger_on_litellm_proxy()
