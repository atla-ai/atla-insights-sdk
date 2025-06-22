import json
from contextvars import ContextVar
from typing import Optional

from opentelemetry.context import Context
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.trace import ReadableSpan, Span, SpanProcessor
from opentelemetry.sdk.trace.export import SimpleSpanProcessor
from opentelemetry.util import types

from ._constants import LOGFIRE_OTEL_TRACES_ENDPOINT, METADATA_MARK, SUCCESS_MARK

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

    def mark_root(self, value: types.AttributeValue) -> None:
        """Mark the root span in the current trace with a value.

        Args:
            value: The value to mark the root span with.

        Raises:
            ValueError: If the root span is not found or is already marked.
        """
        root_span = _root_span.get()
        if root_span is None:
            raise ValueError(
                "Atla marking can only be done within an instrumented function."
            )
        if root_span.attributes is None:
            raise ValueError("Root span attributes are not set.")
        if root_span.attributes.get(SUCCESS_MARK) != -1:
            raise ValueError("Cannot mark the same instrumented function twice.")

        root_span.set_attribute(SUCCESS_MARK, value)


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


def get_atla_root_span_processor() -> AtlaRootSpanProcessor:
    """Get an Atla root span processor.

    :return (AtlaRootSpanProcessor): An Atla root span processor.
    """
    return AtlaRootSpanProcessor()
