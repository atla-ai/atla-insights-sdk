"""LangChain instrumentation."""

import ast
from typing import Any

from wrapt import wrap_function_wrapper

try:
    from openinference.instrumentation import safe_json_dumps
    from openinference.instrumentation.langchain import LangChainInstrumentor
    from openinference.semconv.trace import SpanAttributes
except ImportError as e:
    raise ImportError(
        "LangChain instrumentation needs to be installed. "
        'Please install it via `pip install "atla-insights[langchain]"`.'
    ) from e


def _tools(wrapped: Any, instance: Any, args: Any, kwargs: Any) -> Any:
    """Wrap the tools function to include tool parameters information."""
    # Yield from the original tools instrumentation funtcion.
    yield from wrapped(*args, **kwargs)

    # Get the tool parameters from the run.inputs.input field.
    run = args[0]
    if parameters := run.inputs.get("input"):
        try:
            parameters = ast.literal_eval(parameters)
        except Exception:
            pass
        finally:
            yield SpanAttributes.TOOL_PARAMETERS, safe_json_dumps(parameters)


class AtlaLangChainInstrumentor(LangChainInstrumentor):
    """Atla instrumentor for LangChain."""

    name = "langchain"

    def _instrument(self, **kwargs: Any) -> None:
        # Wrap original _tools functionality that includes tool parameters information.
        wrap_function_wrapper(
            "openinference.instrumentation.langchain._tracer",
            "_tools",
            _tools,
        )

        # Run original instrumentation which uses the wrapped _tools function.
        super()._instrument(**kwargs)
