"""Span processors."""

import json
import warnings
from typing import Optional, Sequence

from opentelemetry.context import Context
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.trace import ReadableSpan, Span, SpanProcessor, TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor, SimpleSpanProcessor

from atla_insights.console_span_exporter import ConsoleSpanExporter
from atla_insights.constants import (
    ENVIRONMENT_MARK,
    EXPERIMENT_RUN_NAMESPACE,
    LIB_VERSIONS,
    LIB_VERSIONS_MARK,
    METADATA_MARK,
    OTEL_TRACES_ENDPOINT,
    SUCCESS_MARK,
    VERSION_MARK,
    __version__,
)
from atla_insights.context import experiment_run_var, root_span_var
from atla_insights.metadata import get_metadata


class AtlaRootSpanProcessor(SpanProcessor):
    """An Atla root span processor."""

    def __init__(self, debug: bool, environment: str) -> None:
        """Initialize the Atla root span processor."""
        self.debug = debug
        self.environment = environment

    def on_start(self, span: Span, parent_context: Optional[Context] = None) -> None:
        """On start span processing."""
        span.set_attribute(VERSION_MARK, __version__)
        span.set_attribute(ENVIRONMENT_MARK, self.environment)

        if self.debug:
            span.set_attribute(LIB_VERSIONS_MARK, LIB_VERSIONS)

        if span.parent is not None:
            return

        root_span_var.set(span)
        span.set_attribute(SUCCESS_MARK, -1)

        if metadata := get_metadata():
            span.set_attribute(METADATA_MARK, json.dumps(metadata))

        if experiment_run := experiment_run_var.get():
            # Experiments are by definition run in dev environment.
            if self.environment != "dev":
                warnings.warn(
                    "Setting environment to 'dev' during experiment run. "
                    "To avoid this warning, update your ATLA_INSIGHTS_ENVIRONMENT "
                    "environment variable or your configure() call.",
                    stacklevel=2,
                )
                span.set_attribute(ENVIRONMENT_MARK, "dev")
            for key, value in experiment_run.items():
                if value is not None:
                    span.set_attribute(f"{EXPERIMENT_RUN_NAMESPACE}.{key}", str(value))

    def on_end(self, span: ReadableSpan) -> None:
        """On end span processing."""
        pass


def get_atla_span_processor(token: str) -> SpanProcessor:
    """Get an Atla span processor.

    :param token (str): The write access token.
    :return (SpanProcessor): An Atla span processor.
    """
    span_exporter = OTLPSpanExporter(
        endpoint=OTEL_TRACES_ENDPOINT,
        headers={"Authorization": f"Bearer {token}"},
    )
    return SimpleSpanProcessor(span_exporter)


def get_atla_console_span_processor() -> BatchSpanProcessor:
    """Get an Atla console span processor.

    :return (BatchSpanProcessor): An Atla console span processor.
    """
    span_exporter = ConsoleSpanExporter()
    return BatchSpanProcessor(span_exporter)


def add_span_processors_to_tracer_provider(
    tracer_provider: TracerProvider,
    token: str,
    additional_span_processors: Optional[Sequence[SpanProcessor]],
    verbose: bool,
    debug: bool,
    environment: str,
) -> None:
    """Adds all relevant span processors to a tracer provider.

    :param tracer_provider (TracerProvider): The tracer provider to add the span
        processors to.
    :param token (str): The write access token.
    :param additional_span_processors (Optional[Sequence[SpanProcessor]]): Additional
        span processors.
    :param verbose (bool): Whether to print verbose output to console.
    :param debug (bool): Whether to log debug outputs.
    :param environment (SUPPORTED_ENVIRONMENT): The environment ("dev" or "prod").
    """
    span_processors = [
        get_atla_span_processor(token),
        AtlaRootSpanProcessor(debug, environment),
    ]

    if additional_span_processors:
        span_processors.extend(additional_span_processors)

    if verbose:
        span_processors.append(get_atla_console_span_processor())

    for span_processor in span_processors:
        tracer_provider.add_span_processor(span_processor)
