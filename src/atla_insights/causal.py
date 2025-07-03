"""Causal-link helpers for Atla Insights.

This module lets developers declare that the next span(s) they create should be
*linked* to one or more existing spans.  It works by storing the source spans
inside a `ContextVar` so the information automatically propagates through async
boundaries and nested function calls.

Public API
==========
- `link_from(span_or_spans)`: context-manager used by end-users.
- `get_current_links() -> list[Span]`: internal helper imported by the
  instrumentation layer to attach `Link` objects when starting a span.
"""

from __future__ import annotations

from contextlib import contextmanager
from contextvars import ContextVar
from typing import Iterable, List

from opentelemetry.trace import Span

# Holds the list of source spans that new spans should link to.
_link_var: ContextVar[List[Span]] = ContextVar("_link_var", default=[])  # noqa: B039


@contextmanager
def link_from(sources: Span | Iterable[Span]):
    """Declare causal links from *sources* to any new spans inside the block.

    Parameters
    ----------
    sources : Span or Iterable[Span]
        The span(s) that should be linked from subsequent spans created while
        this context manager is active.
    """
    # Normalise to a list[Span].  Accept both a single Span and any iterable
    # of Spans.  We check `Span` first to avoid treating it as an iterable of
    # its attributes.
    if isinstance(sources, Span):
        new_links = [sources]
    elif isinstance(sources, Iterable):
        new_links = list(sources)
    else:
        raise TypeError("sources must be a Span or an iterable of Spans")

    # Replace the current value, keeping a token so we can restore it.
    token = _link_var.set(new_links)
    try:
        yield
    finally:
        # Restore the previous value regardless of exceptions.
        _link_var.reset(token)


def get_current_links() -> List[Span]:
    """Return any spans captured by the nearest enclosing ``link_from`` block."""
    return _link_var.get()
