"""BAML instrumentation."""

import logging
from importlib import import_module
from typing import Any, Callable, Collection, Mapping, Optional

try:
    from baml_py import Collector
except ImportError as e:
    raise ImportError(
        "BAML instrumentation needs to be installed. "
        'Please install it via `pip install "atla-insights[baml]"`.'
    ) from e

from openinference.semconv.trace import (
    OpenInferenceSpanKindValues,
    SpanAttributes,
)
from opentelemetry import trace as trace_api
from opentelemetry.instrumentation.instrumentor import (  # type: ignore[attr-defined]
    BaseInstrumentor,
)
from opentelemetry.trace import get_tracer
from wrapt import wrap_function_wrapper

from atla_insights.constants import SUPPORTED_LLM_FORMAT
from atla_insights.parsers import get_llm_parser

logger = logging.getLogger(__name__)

_ATLA_COLLECTOR: Optional[Collector] = None


def _get_baml_collector() -> Collector:
    """Get the BAML collector."""
    global _ATLA_COLLECTOR
    if _ATLA_COLLECTOR is None:
        _ATLA_COLLECTOR = Collector(name="atla-insights")
    return _ATLA_COLLECTOR


class AtlaBamlInstrumentor(BaseInstrumentor):
    """Atla BAML instrumentor class."""

    name = "baml"

    def __init__(self, llm_provider: SUPPORTED_LLM_FORMAT) -> None:
        """Initialize the Atla BAML instrumentator."""
        super().__init__()

        self.llm_parser = get_llm_parser(llm_provider)
        self.tracer = get_tracer("openinference.instrumentation.baml")

        self.original_call_function_sync = None
        self.original_call_function_async = None

    def _call_function_sync_wrapper(
        self,
        wrapped: Callable[..., Any],
        instance: Any,
        args: tuple[Any, ...],
        kwargs: Mapping[str, Any],
    ) -> Any:
        """Wrap the BAML call function."""
        atla_collector = _get_baml_collector()

        original_state = instance.__getstate__()
        original_collectors = original_state.get("baml_options", {}).get("collector")

        new_collectors = [atla_collector]
        if original_collectors is not None:
            if isinstance(original_collectors, list):
                new_collectors.extend(original_collectors)
            else:
                new_collectors.append(original_collectors)

        instance.__setstate__({"baml_options": {"collector": new_collectors}})

        with self.tracer.start_as_current_span(
            name=kwargs.get("function_name", "GenerateSync"),
            attributes={
                SpanAttributes.OPENINFERENCE_SPAN_KIND: (
                    OpenInferenceSpanKindValues.LLM.value
                ),
            },
            record_exception=False,
            set_status_on_exception=False,
        ) as span:
            try:
                result = wrapped(*args, **kwargs)
            except Exception as exception:
                span.set_status(
                    trace_api.Status(trace_api.StatusCode.ERROR, str(exception))
                )
                span.record_exception(exception)
                raise

            span.set_status(trace_api.StatusCode.OK)

            if (
                atla_collector.last is not None
                and atla_collector.last.selected_call is not None
            ):
                if llm_request := atla_collector.last.selected_call.http_request:
                    request_body = llm_request.body.json()
                    span.set_attributes(
                        dict(self.llm_parser.parse_request_body(request_body))
                    )

                if llm_response := atla_collector.last.selected_call.http_response:
                    response_body = llm_response.body.json()
                    span.set_attributes(
                        dict(self.llm_parser.parse_response_body(response_body))
                    )

        return result

    async def _call_function_async_wrapper(
        self,
        wrapped: Callable[..., Any],
        instance: Any,
        args: tuple[Any, ...],
        kwargs: Mapping[str, Any],
    ) -> Any:
        """Wrap the BAML async call function."""
        atla_collector = _get_baml_collector()

        original_state = instance.__getstate__()
        original_collectors = original_state.get("baml_options", {}).get("collector")

        new_collectors = [atla_collector]
        if original_collectors is not None:
            if isinstance(original_collectors, list):
                new_collectors.extend(original_collectors)
            else:
                new_collectors.append(original_collectors)

        instance.__setstate__({"baml_options": {"collector": new_collectors}})

        with self.tracer.start_as_current_span(
            name=kwargs.get("function_name", "GenerateAsync"),
            attributes={
                SpanAttributes.OPENINFERENCE_SPAN_KIND: (
                    OpenInferenceSpanKindValues.LLM.value
                ),
            },
            record_exception=False,
            set_status_on_exception=False,
        ) as span:
            try:
                result = await wrapped(*args, **kwargs)
            except Exception as exception:
                span.set_status(
                    trace_api.Status(trace_api.StatusCode.ERROR, str(exception))
                )
                span.record_exception(exception)
                raise

            span.set_status(trace_api.StatusCode.OK)

            if (
                atla_collector.last is not None
                and atla_collector.last.selected_call is not None
            ):
                if llm_request := atla_collector.last.selected_call.http_request:
                    request_body = llm_request.body.json()
                    span.set_attributes(
                        dict(self.llm_parser.parse_request_body(request_body))
                    )

                if llm_response := atla_collector.last.selected_call.http_response:
                    response_body = llm_response.body.json()
                    span.set_attributes(
                        dict(self.llm_parser.parse_response_body(response_body))
                    )

        return result

    def instrumentation_dependencies(self) -> Collection[str]:
        """Return a list of python packages that the will be instrumented."""
        return ("baml-py",)

    def _instrument(self, **kwargs: Any) -> None:
        self.original_call_function_sync = getattr(
            import_module("baml_client.runtime").DoNotUseDirectlyCallManager,
            "call_function_sync",
            None,
        )
        wrap_function_wrapper(
            module="baml_client.runtime",
            name="DoNotUseDirectlyCallManager.call_function_sync",
            wrapper=self._call_function_sync_wrapper,
        )

        self.original_call_function_async = getattr(
            import_module("baml_client.runtime").DoNotUseDirectlyCallManager,
            "call_function_async",
            None,
        )
        wrap_function_wrapper(
            module="baml_client.runtime",
            name="DoNotUseDirectlyCallManager.call_function_async",
            wrapper=self._call_function_async_wrapper,
        )

    def _uninstrument(self, **kwargs: Any) -> None:
        if self.original_call_function_sync is not None:
            runtime_module = import_module("baml_client.runtime")
            runtime_module.DoNotUseDirectlyCallManager.call_function_sync = (
                self.original_call_function_sync
            )
            self.original_call_function_sync = None

        if self.original_call_function_async is not None:
            runtime_module = import_module("baml_client.runtime")
            runtime_module.DoNotUseDirectlyCallManager.call_function_async = (
                self.original_call_function_async
            )
            self.original_call_function_async = None
