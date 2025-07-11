"""BAML instrumentation."""

import importlib
import importlib.util
import logging
from importlib import import_module
from typing import Any, Callable, Collection, Generator, Mapping

from openinference.semconv.trace import (
    OpenInferenceLLMProviderValues,
    OpenInferenceLLMSystemValues,
    OpenInferenceMimeTypeValues,
    OpenInferenceSpanKindValues,
    SpanAttributes,
)
from opentelemetry import trace as trace_api
from opentelemetry.instrumentation.instrumentor import BaseInstrumentor
from opentelemetry.trace import get_tracer
from wrapt import wrap_function_wrapper

from atla_insights.constants import SUPPORTED_LLM_FORMAT

logger = logging.getLogger(__name__)

_ATLA_COLLECTOR = None


def _get_baml_collector() -> Any:
    """Get the BAML collector."""
    from baml_py import Collector

    global _ATLA_COLLECTOR
    if _ATLA_COLLECTOR is None:
        _ATLA_COLLECTOR = Collector(name="atla-insights")
    return _ATLA_COLLECTOR


def _parse_anthropic_request_body(
    request: dict[str, Any],
) -> Generator[tuple[str, Any], None, None]:
    """Parse the Anthropic request."""
    from openinference.instrumentation.anthropic._wrappers import (
        _get_llm_input_messages,
        _get_llm_tools,
    )

    yield SpanAttributes.LLM_PROVIDER, OpenInferenceLLMProviderValues.ANTHROPIC.value
    yield SpanAttributes.LLM_SYSTEM, OpenInferenceLLMSystemValues.ANTHROPIC.value

    if model := request.get("model", request.get("anthropic_version")):
        yield SpanAttributes.LLM_MODEL_NAME, model

    if messages := request.get("messages"):
        yield from _get_llm_input_messages(messages)

    if tools := request.get("tools"):
        yield from _get_llm_tools(tools)


def _parse_llm_request_body(
    request: dict[str, Any],
    llm_provider: SUPPORTED_LLM_FORMAT,
) -> Generator[tuple[str, Any], None, None]:
    """Parse the LLM request."""
    match llm_provider:
        case "anthropic":
            yield from _parse_anthropic_request_body(request)
        case _:
            logger.error(f"Unsupported LLM provider: {llm_provider}")


def _parse_anthropic_response_body(
    response: dict[str, Any],
) -> Generator[tuple[str, Any], None, None]:
    """Parse the Anthropic response."""
    from anthropic.types.message import Message
    from openinference.instrumentation.anthropic._wrappers import _get_output_messages

    try:
        message = Message(**response)
    except Exception as e:
        logger.error(f"Failed to parse Anthropic response: {e}")
        return

    yield from _get_output_messages(message)


def _parse_llm_response_body(
    response: dict[str, Any],
    llm_provider: SUPPORTED_LLM_FORMAT,
) -> Generator[tuple[str, Any], None, None]:
    """Parse the LLM response."""
    match llm_provider:
        case "anthropic":
            yield from _parse_anthropic_response_body(response)
        case _:
            logger.error(f"Unsupported LLM provider: {llm_provider}")


class AtlaBamlInstrumentor(BaseInstrumentor):
    """Atla BAML instrumentor class."""

    name = "baml"

    def __init__(self, llm_provider: SUPPORTED_LLM_FORMAT) -> None:
        """Initialize the Atla BAML instrumentator."""
        super().__init__()

        match llm_provider:
            case "anthropic":
                if (
                    importlib.util.find_spec("openinference.instrumentation.anthropic")
                    is None
                ):
                    raise ImportError(
                        "Anthropic instrumentation needs to be installed. "
                        'Please install it via `pip install "atla-insights[anthropic]"`.'
                    )

            case _:
                raise ValueError(f"Unsupported LLM provider: {llm_provider}")

        self.tracer = get_tracer("openinference.instrumentation.baml")
        self.llm_provider: SUPPORTED_LLM_FORMAT = llm_provider

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

        instance.__setstate__({"baml_options": {"collector": atla_collector}})

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
                    span.set_attributes(
                        {
                            SpanAttributes.INPUT_VALUE: llm_request.body.text(),
                            SpanAttributes.INPUT_MIME_TYPE: (
                                OpenInferenceMimeTypeValues.TEXT.value
                            ),
                        }
                    )

                    span.set_attributes(
                        dict(
                            _parse_llm_request_body(
                                llm_request.body.json(), self.llm_provider
                            )
                        )
                    )

                if llm_response := atla_collector.last.selected_call.http_response:
                    span.set_attributes(
                        {
                            SpanAttributes.OUTPUT_VALUE: llm_response.body.text(),
                            SpanAttributes.OUTPUT_MIME_TYPE: (
                                OpenInferenceMimeTypeValues.JSON.value
                            ),
                        }
                    )
                    span.set_attributes(
                        dict(
                            _parse_llm_response_body(
                                llm_response.body.json(), self.llm_provider
                            )
                        )
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

        instance.__setstate__({"baml_options": {"collector": atla_collector}})

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
                    span.set_attributes(
                        {
                            SpanAttributes.INPUT_VALUE: llm_request.body.text(),
                            SpanAttributes.INPUT_MIME_TYPE: (
                                OpenInferenceMimeTypeValues.TEXT.value
                            ),
                        }
                    )

                    span.set_attributes(
                        dict(
                            _parse_llm_request_body(
                                llm_request.body.json(), self.llm_provider
                            )
                        )
                    )

                if llm_response := atla_collector.last.selected_call.http_response:
                    span.set_attributes(
                        {
                            SpanAttributes.OUTPUT_VALUE: llm_response.body.text(),
                            SpanAttributes.OUTPUT_MIME_TYPE: (
                                OpenInferenceMimeTypeValues.JSON.value
                            ),
                        }
                    )
                    span.set_attributes(
                        dict(
                            _parse_llm_response_body(
                                llm_response.body.json(), self.llm_provider
                            )
                        )
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
