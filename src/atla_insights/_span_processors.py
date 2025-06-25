import json
from contextvars import ContextVar
from typing import Optional

from opentelemetry.context import Context
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.trace import ReadableSpan, Span, SpanProcessor
from opentelemetry.sdk.trace.export import SimpleSpanProcessor

from atla_insights._constants import (
    LOGFIRE_OTEL_TRACES_ENDPOINT,
    METADATA_MARK,
    SUCCESS_MARK,
)

_metadata: ContextVar[Optional[dict[str, str]]] = ContextVar("_metadata", default=None)
_root_span: ContextVar[Optional[Span]] = ContextVar("_root_span", default=None)


class AtlaRootSpanProcessor(SpanProcessor):
    """An Atla root span processor."""

    def on_start(self, span: Span, parent_context: Optional[Context] = None) -> None:
        if span.parent is not None:
            return

        _root_span.set(span)
        span.set_attribute(SUCCESS_MARK, -1)

        if metadata := _metadata.get():
            span.set_attribute(METADATA_MARK, json.dumps(metadata))

    def on_end(self, span: ReadableSpan) -> None:
        pass


def get_atla_span_processor(token: str) -> SpanProcessor:
    """Get an Atla span processor.

    :param token (str): The write access token.
    :return (SpanProcessor): An Atla span processor.
    """
    span_exporter = OTLPSpanExporter(
        endpoint=LOGFIRE_OTEL_TRACES_ENDPOINT,
        headers={"Authorization": f"Bearer {token}"},
    )
    return SimpleSpanProcessor(span_exporter)
