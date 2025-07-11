"""Agno instrumentation."""

from typing import Any

from opentelemetry.instrumentation.instrumentor import BaseInstrumentor


class AtlaBamlInstrumentor(BaseInstrumentor):
    """Atla BAML instrumentor class."""

    name = "baml"

    def _instrument(self, **kwargs: Any) -> None:
        pass

    def _uninstrument(self, **kwargs: Any) -> None:
        pass
