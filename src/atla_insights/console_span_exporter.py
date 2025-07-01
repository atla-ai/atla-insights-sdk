"""Console span exporter."""

import os
import sys
from collections.abc import Sequence
from datetime import datetime, timezone
from textwrap import indent as indent_text
from typing import List, Literal, Optional, TextIO, Tuple, cast

from opentelemetry.sdk.trace import Event, ReadableSpan
from opentelemetry.sdk.trace.export import SpanExporter, SpanExportResult
from rich.console import Console, Group
from rich.syntax import Syntax
from rich.text import Text

ConsoleColorsValues = Literal["auto", "always", "never"]
ONE_SECOND_IN_NANOSECONDS = 1_000_000_000
TextParts = List[Tuple[str, str]]


class ConsoleSpanExporter(SpanExporter):
    """The ConsoleSpanExporter prints spans to the console."""

    def __init__(
        self,
        output: TextIO | None = None,
        colors: ConsoleColorsValues = "auto",
        include_timestamp: bool = True,
    ) -> None:
        """Initialize the ConsoleSpanExporter.

        :param output (TextIO | None): The output stream to write to.
            Defaults to `sys.stdout`.
        :param colors (ConsoleColorsValues): The color mode to use. Defaults to `"auto"`.
        :param include_timestamp (bool): Whether to include the timestamp in the output.
            Defaults to `True`.
        """
        self._output = output or sys.stdout
        if colors == "auto":
            force_terminal = None
        else:
            force_terminal = colors == "always"
        self._console: Optional[Console] = Console(
            color_system="standard" if os.environ.get("PYTEST_VERSION") else "auto",
            file=self._output,
            force_terminal=force_terminal,
            highlight=False,
            markup=False,
            soft_wrap=True,
        )
        if not self._console.is_terminal:
            self._console = None

        self._include_timestamp = include_timestamp
        self._timestamp_indent = 13 if include_timestamp else 0

    def export(self, spans: Sequence[ReadableSpan]) -> SpanExportResult:
        """Export the spans to the console."""
        span_id_to_span = {span.context.span_id: span for span in spans if span.context}
        indent_cache: dict[int, int] = {}

        def get_indent_level(span: ReadableSpan) -> int:
            if not span.context:
                return 0

            span_id = span.context.span_id

            if span_id in indent_cache:
                return indent_cache[span_id]

            level = 0
            current = span
            path = []

            while current.parent is not None:
                parent_span = span_id_to_span.get(current.parent.span_id)
                if parent_span is None:
                    level += 1
                    break

                if not parent_span.context:
                    break

                parent_id = parent_span.context.span_id
                if parent_id in indent_cache:
                    level += indent_cache[parent_id] + 1
                    break

                if current.context:
                    path.append((current.context.span_id, level))
                current = parent_span
                level += 1

            indent_cache[span_id] = level

            for path_span_id, path_level in reversed(path):
                if path_span_id not in indent_cache:
                    indent_cache[path_span_id] = level - path_level

            return level

        for span in sorted(spans, key=lambda s: s.start_time or 0):
            indent_level = get_indent_level(span)
            self._print_span(span, indent_level)

        return SpanExportResult.SUCCESS

    def _print_span(self, span: ReadableSpan, indent: int = 0):
        """Build up a summary of the span, including formatting for rich, then print it.

        :param span (ReadableSpan): The span to print.
        :param indent (int): The indent level. Defaults to 0.
        """
        _msg, parts = self._span_text_parts(span, indent)

        indent_str = (self._timestamp_indent + indent * 2) * " "

        if self._console:
            self._console.print(Text.assemble(*parts))
        elif self._output and not self._output.closed:
            print("".join(text for text, _style in parts), file=self._output)

        exc_event = next(
            (event for event in span.events or [] if event.name == "exception"), None
        )
        self._print_exc_info(exc_event, indent_str)

    def _span_text_parts(self, span: ReadableSpan, indent: int) -> tuple[str, TextParts]:
        """Build up a summary of the span, including formatting for rich, then print it.

        :param span (ReadableSpan): The span to print.
        :param indent (int): The indent level. Defaults to `0`.
        :return (tuple[str, TextParts]): The formatted message or span name and parts
        containing basic span information.

        The following information is included:
        * timestamp
        * message (maybe indented)
        * tags (if `self._include_tags` is True)

        The log level may be indicated by the color of the message.
        """
        parts: TextParts = []
        if self._include_timestamp:
            ts = datetime.fromtimestamp(
                (span.start_time or 0) / ONE_SECOND_IN_NANOSECONDS, tz=timezone.utc
            )
            ts_str = f"{ts:%H:%M:%S.%f}"[:-3]
            parts += [(ts_str, "green"), (" ", "")]

        if indent:
            parts += [(indent * "  ", "")]

        parts += [(span.name or "Unnamed Span", "")]

        return span.name, parts

    def _print_exc_info(self, exc_event: Event | None, indent_str: str) -> None:
        """Print exception information if an exception event is present.

        :param exc_event (Event | None): The exception event to print.
        :param indent_str (str): The indent string.
        """
        if exc_event is None or not exc_event.attributes:
            return

        exc_type = cast(str, exc_event.attributes.get("exception.type"))
        exc_msg = cast(str, exc_event.attributes.get("exception.message"))
        exc_tb = cast(str, exc_event.attributes.get("exception.stacktrace"))

        if self._console:
            barrier = Text(indent_str + "│ ", style="blue", end="")
            exc_type_rich = Text(f"{exc_type}: ", end="", style="bold red")
            exc_msg_rich = Text(exc_msg)
            indented_code = indent_text(exc_tb, indent_str + "│ ")
            exc_tb_rich = Syntax(indented_code, "python", background_color="default")
            self._console.print(Group(barrier, exc_type_rich, exc_msg_rich), exc_tb_rich)
        elif self._output and not self._output.closed:
            out = [f"{indent_str}│ {exc_type}: {exc_msg}"]
            out += [indent_text(exc_tb, indent_str + "│ ")]
            print("\n".join(out), file=self._output)

    def force_flush(self, timeout_millis: int = 0) -> bool:
        """Force flush all spans, does nothing for this exporter."""
        return True
