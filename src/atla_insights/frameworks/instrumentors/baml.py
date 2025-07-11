"""Agno instrumentation."""

from typing import Any, Callable, Collection, Mapping

from baml_py import Collector
from opentelemetry.instrumentation.instrumentor import BaseInstrumentor
from wrapt import wrap_function_wrapper

atla_collector = Collector(name="atla-insights")


def call_function_sync_wrapper(
    wrapped: Callable[..., Any],
    instance: Any,
    args: tuple[Any, ...],
    kwargs: Mapping[str, Any],
) -> None:
    breakpoint()
    return wrapped(*args, **kwargs)


class AtlaBamlInstrumentor(BaseInstrumentor):
    """Atla BAML instrumentor class."""

    name = "baml"

    def instrumentation_dependencies(self) -> Collection[str]:
        """Return a list of python packages with versions that the will be instrumented.

        The format should be the same as used in requirements.txt or pyproject.toml.

        For example, if an instrumentation instruments requests 1.x, this method should look
        like:

            def instrumentation_dependencies(self) -> Collection[str]:
                return ['requests ~= 1.0']

        This will ensure that the instrumentation will only be used when the specified library
        is present in the environment.
        """
        return ("baml-py",)

    def _instrument(self, **kwargs: Any) -> None:
        wrap_function_wrapper(
            module="baml_client.runtime",
            name="DoNotUseDirectlyCallManager.call_function_sync",
            wrapper=call_function_sync_wrapper,
        )
        pass

    def _uninstrument(self, **kwargs: Any) -> None:
        pass
