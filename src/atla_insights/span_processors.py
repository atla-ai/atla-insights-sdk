"""Span processors."""

import json
from typing import Optional

from opentelemetry.context import Context
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.trace import ReadableSpan, Span, SpanProcessor
from opentelemetry.sdk.trace.export import BatchSpanProcessor, SimpleSpanProcessor

from atla_insights.console_span_exporter import ConsoleSpanExporter
from atla_insights.constants import METADATA_MARK, OTEL_TRACES_ENDPOINT, SUCCESS_MARK
from atla_insights.context import metadata_var, root_span_var


class AtlaRootSpanProcessor(SpanProcessor):
    """An Atla root span processor."""

    def on_start(self, span: Span, parent_context: Optional[Context] = None) -> None:
        """On start span processing."""
        if span.parent is not None:
            return

        root_span_var.set(span)
        span.set_attribute(SUCCESS_MARK, -1)

        if metadata := metadata_var.get():
            span.set_attribute(METADATA_MARK, json.dumps(metadata))

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
