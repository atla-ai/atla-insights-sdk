"""LangChain instrumentation."""

import ast
from typing import Any

from openinference.instrumentation import safe_json_dumps
from openinference.instrumentation.langchain import LangChainInstrumentor
from openinference.semconv.trace import SpanAttributes
from wrapt import wrap_function_wrapper


def _tools(wrapped: Any, instance: Any, args: Any, kwargs: Any) -> Any:
    """Wrap the tools function to include tool parameters information."""
    yield from wrapped(*args, **kwargs)

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

    def _instrument(self, **kwargs: Any) -> None:
        wrap_function_wrapper(
            "openinference.instrumentation.langchain._tracer",
            "_tools",
            _tools,
        )
        super()._instrument(**kwargs)
