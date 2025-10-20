"""Span processors."""

import json
import os
from typing import Optional

from opentelemetry.context import Context
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.trace import ReadableSpan, Span, SpanProcessor

from atla_insights.constants import (
    ENVIRONMENT_MARK,
    EXPERIMENT_NAMESPACE,
    GIT_TRACKING_DISABLED_ENV_VAR,
    LIB_VERSIONS,
    LIB_VERSIONS_MARK,
    METADATA_MARK,
    OTEL_TRACES_ENDPOINT,
    SUCCESS_MARK,
    VERSION_MARK,
    __version__,
)
from atla_insights.context import experiment_var, root_span_var
from atla_insights.git_info import GitInfo
from atla_insights.metadata import get_metadata


class AtlaRootSpanProcessor(SpanProcessor):
    """An Atla root span processor."""

    def __init__(self, debug: bool, environment: str) -> None:
        """Initialize the Atla root span processor."""
        self.debug = debug
        self.environment = environment

        self.git_info = GitInfo()

    def on_start(self, span: Span, parent_context: Optional[Context] = None) -> None:
        """On start span processing."""
        span.set_attribute(VERSION_MARK, __version__)
        span.set_attribute(ENVIRONMENT_MARK, self.environment)

        if not os.getenv(GIT_TRACKING_DISABLED_ENV_VAR):
            for attr_name, attr_value in self.git_info.attributes.items():
                if attr_value is not None:
                    span.set_attribute(attr_name, attr_value)

        if self.debug:
            span.set_attribute(LIB_VERSIONS_MARK, LIB_VERSIONS)

        if span.parent is not None:
            return

        root_span_var.set(span)
        span.set_attribute(SUCCESS_MARK, -1)

        if metadata := get_metadata():
            span.set_attribute(METADATA_MARK, json.dumps(metadata))

        if experiment := experiment_var.get():
            # Experiments are by definition run in dev environment.
            span.set_attribute(ENVIRONMENT_MARK, "dev")
            for key, value in experiment.items():
                if value is not None:
                    span.set_attribute(f"{EXPERIMENT_NAMESPACE}.{key}", str(value))

    def on_end(self, span: ReadableSpan) -> None:
        """On end span processing."""
        pass


def get_atla_span_exporter(token: str) -> OTLPSpanExporter:
    """Get the Atla span exporter."""
    return OTLPSpanExporter(
        endpoint=OTEL_TRACES_ENDPOINT,
        headers={"Authorization": f"Bearer {token}"},
    )
