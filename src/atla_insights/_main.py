"""Core functionality for the atla_insights package."""

import importlib
import json
import logging
import os
from contextlib import contextmanager
from typing import (
    ContextManager,
    Literal,
    Optional,
    Sequence,
)

import logfire
import opentelemetry.trace
from opentelemetry import trace
from opentelemetry.instrumentation.instrumentor import (  # type: ignore[attr-defined]
    BaseInstrumentor,
)
from opentelemetry.sdk.environment_variables import OTEL_ATTRIBUTE_COUNT_LIMIT
from opentelemetry.sdk.trace import SpanProcessor
from opentelemetry.trace import Tracer, TracerProvider

from atla_insights._constants import (
    DEFAULT_OTEL_ATTRIBUTE_COUNT_LIMIT,
    METADATA_MARK,
    SUCCESS_MARK,
)
from atla_insights._span_processors import (
    AtlaRootSpanProcessor,
    _metadata,
    _root_span,
    get_atla_span_processor,
)
from atla_insights._utils import validate_metadata

logger = logging.getLogger("atla_insights")


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
        self._maybe_reset_tracer_provider()

        validate_metadata(metadata)
        _metadata.set(metadata)

        additional_span_processors = additional_span_processors or []
        span_processors = [
            get_atla_span_processor(token),
            AtlaRootSpanProcessor(),
            *additional_span_processors,
        ]

        logfire_instance = logfire.configure(
            additional_span_processors=span_processors,
            console=None if verbose else False,
            environment=os.getenv("_ATLA_ENV", "prod"),
            send_to_logfire=False,
            scrubbing=False,
        )
        self.tracer = logfire_instance._get_tracer(is_span_tracer=True)
        self.configured = True

        logger.info("Atla insights configured correctly ✅")

    def _maybe_reset_tracer_provider(self) -> None:
        """Reset the existing OpenTelemetry tracer provider, if one exists.

        Removes any existing tracer provider to allow the Atla tracer provider to get
        initialized correctly. OpenTelemetry tracer providers cannot be re-initialized, so
        we need to reload the module.
        """
        if isinstance(trace.get_tracer_provider(), TracerProvider):
            importlib.reload(opentelemetry.trace)

    def _mark_root_span(self, value: Literal[0, 1]) -> None:
        """Mark the root span in the current trace with a value."""
        if not self.configured:
            raise ValueError(
                "Cannot mark trace before running the atla `configure` method."
            )
        root_span = _root_span.get()
        if root_span is None:
            raise ValueError(
                "Atla marking can only be done within an instrumented function."
            )
        root_span.set_attribute(SUCCESS_MARK, value)

    def mark_success(self) -> None:
        """Mark the root span in the current trace as successful."""
        self._mark_root_span(1)
        logger.info("Marked trace as success ✅")

    def mark_failure(self) -> None:
        """Mark the root span in the current trace as failed."""
        self._mark_root_span(0)
        logger.info("Marked trace as failure ❌")

    def get_metadata(self) -> Optional[dict[str, str]]:
        """Get the metadata for the current trace."""
        return _metadata.get()

    def set_metadata(self, metadata: dict[str, str]) -> None:
        """Set the metadata for the current trace."""
        validate_metadata(metadata)

        _metadata.set(metadata)
        if root_span := _root_span.get():
            # If the root span already exists, we can assign the metadata to it.
            # If not, it will be assigned the `_metadata` context var on creation.
            root_span.set_attribute(METADATA_MARK, json.dumps(metadata))

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

get_metadata = ATLA_INSTANCE.get_metadata
set_metadata = ATLA_INSTANCE.set_metadata

mark_success = ATLA_INSTANCE.mark_success
mark_failure = ATLA_INSTANCE.mark_failure
