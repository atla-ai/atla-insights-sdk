"""Core functionality for the atla_insights package."""

import logging
import os
from contextlib import contextmanager
from typing import ContextManager, Optional, Sequence

from opentelemetry.instrumentation.instrumentor import (  # type: ignore[attr-defined]
    BaseInstrumentor,
)
from opentelemetry.sdk.environment_variables import OTEL_ATTRIBUTE_COUNT_LIMIT
from opentelemetry.sdk.trace import SpanProcessor, TracerProvider
from opentelemetry.trace import Tracer, set_tracer_provider

from atla_insights.constants import DEFAULT_OTEL_ATTRIBUTE_COUNT_LIMIT, OTEL_MODULE_NAME
from atla_insights.metadata import set_metadata
from atla_insights.span_processors import (
    AtlaRootSpanProcessor,
    get_atla_console_span_processor,
    get_atla_span_processor,
)
from atla_insights.utils import maybe_get_existing_tracer_provider

logger = logging.getLogger(OTEL_MODULE_NAME)


# Override the OTEL default attribute count limit (128), if not user-specified. This is
# because we use separate attributes to store e.g. message history, available tools, etc.
# see: https://opentelemetry-python.readthedocs.io/en/latest/sdk/environment_variables.html#opentelemetry.sdk.environment_variables.OTEL_ATTRIBUTE_COUNT_LIMIT
if os.environ.get(OTEL_ATTRIBUTE_COUNT_LIMIT) is None:
    os.environ[OTEL_ATTRIBUTE_COUNT_LIMIT] = str(DEFAULT_OTEL_ATTRIBUTE_COUNT_LIMIT)


class AtlaInsights:
    """Atla insights."""

    def __init__(self) -> None:
        """Initialize Atla insights."""
        self._active_instrumentors: dict[str, Sequence[BaseInstrumentor]] = {}

        self.configured = False
        self.tracer: Optional[Tracer] = None

    def configure(
        self,
        token: str,
        metadata: Optional[dict[str, str]] = None,
        additional_span_processors: Optional[Sequence[SpanProcessor]] = None,
        verbose: bool = True,
    ) -> None:
        """Configure Atla insights.

        :param token (str): The write access token.
        :param metadata (Optional[dict[str, str]]): A dictionary of metadata to be added
            to the trace.
        :param additional_span_processors (Optional[Sequence[SpanProcessor]]): Additional
            span processors. Defaults to `None`.
        :param verbose (bool): Whether to print verbose output to console.
            Defaults to `True`.
        """
        if metadata is not None:
            set_metadata(metadata)

        additional_span_processors = additional_span_processors or []
        span_processors = [
            get_atla_span_processor(token),
            AtlaRootSpanProcessor(),
            *additional_span_processors,
        ]

        if verbose:
            span_processors.append(get_atla_console_span_processor())

        self.tracer_provider = self._setup_tracer_provider()
        self.tracer = self.tracer_provider.get_tracer(OTEL_MODULE_NAME)

        for processor in span_processors:
            self.tracer_provider.add_span_processor(processor)

        self.configured = True
        logger.info("Atla insights configured correctly ✅")

    def _setup_tracer_provider(self) -> TracerProvider:
        """Setup the tracer provider.

        If a (non-proxy) tracer provider is already set, we return it. All Atla-specific
        telemetry will be added to the existing functionality attached to this tracer
        provider.

        If no tracer provider is set, we create a new one and set it as the global tracer
        provider.

        :return (TracerProvider): The tracer provider.
        """
        if existing_tracer_provider := maybe_get_existing_tracer_provider():
            return existing_tracer_provider

        # If no existing tracer provider is found, we create a new one and set it as the
        # global tracer provider.
        new_tracer_provider = TracerProvider()
        set_tracer_provider(new_tracer_provider)
        return new_tracer_provider

    def instrument_service(
        self, service: str, instrumentors: Sequence[BaseInstrumentor]
    ) -> ContextManager[None]:
        """Instrument a service (i.e. framework or LLM provider).

        This function creates a context manager that instruments a service, within its
        context. It also registers the relevant instrumentors for the service, so that
        they can be uninstrumented later.

        :param service (str): The service to instrument.
        :param instrumentors (Sequence[BaseInstrumentor]): The instrumentors to use.
        :return (ContextManager[None]): A context manager that instruments the provider.
        """
        # If the service is already registered as instrumented, first uninstrument it.
        if service in self._active_instrumentors:
            logger.warning(f"Attempting to instrument already instrumented {service}")
            self.uninstrument_service(service)

        # Call each instrumentor for the service.
        for instrumentor in instrumentors:
            instrumentor.instrument()

        # Register the instrumentors for the service.
        self._active_instrumentors[service] = instrumentors

        # Create a instrumentation context manager that uninstruments on context end.
        @contextmanager
        def instrumented_context():
            try:
                yield
            finally:
                self.uninstrument_service(service)

        return instrumented_context()

    def uninstrument_service(self, service: str) -> None:
        """Uninstrument a service (i.e. framework or LLM provider).

        This function will look up a given service in its internal registry of
        instrumented services, and (if found) uninstrument it & remove it from the
        registry.

        :param service (str): The service to uninstrument.
        """
        # If service is unregistered, we can't uninstrument it.
        if service not in self._active_instrumentors.keys():
            logger.warning(
                f"Attempting to uninstrument {service} which was not instrumented."
            )
            return

        # Uninstrument the service's instrumentors & remove its mention from the registry.
        instrumentors = self._active_instrumentors.pop(service)
        for instrumentor in instrumentors:
            instrumentor.uninstrument()


ATLA_INSTANCE = AtlaInsights()

configure = ATLA_INSTANCE.configure
