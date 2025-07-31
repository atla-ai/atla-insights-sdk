"""OpenAI instrumentation."""

import openai
import opentelemetry.trace as trace_api
from wrapt import wrap_function_wrapper

try:
    from openinference.instrumentation import OITracer, TraceConfig
    from openinference.instrumentation.openai import (
        OpenAIInstrumentor,
        __version__,
        _AsyncRequest,
        _Request,
    )
except ImportError as e:
    raise ImportError(
        "OpenAI instrumentation needs to be installed. "
        'Please install it via `pip install "atla-insights[openai]"`.'
    ) from e


class AtlaOpenAIInstrumentor(OpenAIInstrumentor):
    """Atla OpenAI instrumentor class."""

    name = "openai"

    def __init__(self, **kwargs) -> None:
        """Initialize the OpenAI instrumentor."""
        super().__init__(**kwargs)

        self._original_azure_request = None
        self._original_async_azure_request = None

    def _instrument(self, **kwargs) -> None:
        super()._instrument(**kwargs)
        tracer_provider = trace_api.get_tracer_provider()
        tracer = OITracer(
            trace_api.get_tracer(__name__, __version__, tracer_provider),
            config=TraceConfig(),
        )

        self._original_azure_request = openai.AzureOpenAI.request
        wrap_function_wrapper(
            module="openai",
            name="AzureOpenAI.request",
            wrapper=_Request(tracer=tracer, openai=openai),
        )

        self._original_async_azure_request = openai.AsyncAzureOpenAI.request
        wrap_function_wrapper(
            module="openai",
            name="AsyncAzureOpenAI.request",
            wrapper=_AsyncRequest(tracer=tracer, openai=openai),
        )

    def _uninstrument(self, **kwargs) -> None:
        """Uninstrument the OpenAI instrumentor."""
        super()._uninstrument(**kwargs)

        if self._original_azure_request is not None:
            openai.AzureOpenAI.request = self._original_azure_request
            self._original_azure_request = None

        if self._original_async_azure_request is not None:
            openai.AsyncAzureOpenAI.request = self._original_async_azure_request
            self._original_async_azure_request = None
