"""BAML instrumentation."""

import logging
from importlib import import_module
from typing import Any, Callable, Collection, Mapping

try:
    from baml_py import Collector
except ImportError as e:
    raise ImportError(
        "BAML instrumentation needs to be installed. "
        'Please install it via `pip install "atla-insights[baml]"`.'
    ) from e

from openinference.semconv.trace import (
    MessageAttributes,
    OpenInferenceSpanKindValues,
    SpanAttributes,
)
from opentelemetry import trace as trace_api
from opentelemetry.instrumentation.instrumentor import (  # type: ignore[attr-defined]
    BaseInstrumentor,
)
from opentelemetry.trace import get_tracer
from pydantic import BaseModel
from wrapt import wrap_function_wrapper

from atla_insights.constants import SUPPORTED_LLM_FORMAT
from atla_insights.parsers import get_llm_parser

logger = logging.getLogger(__name__)


def _get_updated_collectors(
    original_state: Mapping[str, Any],
    atla_collector: Collector,
) -> list[Collector]:
    """Get the updated collectors."""
    original_collectors = original_state.get("baml_options", {}).get("collector")

    new_collectors = [atla_collector]
    if original_collectors is not None:
        if isinstance(original_collectors, list):
            new_collectors.extend(
                [
                    collector
                    for collector in original_collectors
                    if collector != atla_collector
                ]
            )
        elif original_collectors != atla_collector:
            new_collectors.append(original_collectors)

    return new_collectors


class AtlaBamlInstrumentor(BaseInstrumentor):
    """Atla BAML instrumentor class."""

    name = "baml"

    def __init__(self, llm_provider: SUPPORTED_LLM_FORMAT) -> None:
        """Initialize the Atla BAML instrumentator."""
        super().__init__()

        self.atla_collector = Collector(name="atla-insights")
        self.llm_parser = get_llm_parser(llm_provider)
        self.tracer = get_tracer("openinference.instrumentation.baml")

        self.original_call_function_sync = None
        self.original_create_stream_function_sync = None
        self.original_stream_function_sync = None
        self.original_stream_final_response_function_sync = None

        self.original_call_function_async = None
        self.original_create_stream_function_async = None
        self.original_stream_function_async = None
        self.original_stream_final_response_function_async = None

    def _call_function_sync_wrapper(
        self,
        wrapped: Callable[..., Any],
        instance: Any,
        args: tuple[Any, ...],
        kwargs: Mapping[str, Any],
    ) -> Any:
        """Wrap the BAML call function."""
        new_collectors = _get_updated_collectors(
            instance.__getstate__(), self.atla_collector
        )
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
                self.atla_collector.last is not None
                and self.atla_collector.last.selected_call is not None
            ):
                if llm_request := self.atla_collector.last.selected_call.http_request:
                    request_body = llm_request.body.json()
                    span.set_attributes(
                        dict(self.llm_parser.parse_request_body(request_body))
                    )

                if llm_response := self.atla_collector.last.selected_call.http_response:
                    response_body = llm_response.body.json()
                    span.set_attributes(
                        dict(self.llm_parser.parse_response_body(response_body))
                    )

        return result

    def _create_stream_wrapper(
        self,
        wrapped: Callable[..., Any],
        instance: Any,
        args: tuple[Any, ...],
        kwargs: Mapping[str, Any],
    ) -> Any:
        """Wrap the BAML create sync stream function."""
        new_collectors = _get_updated_collectors(
            instance.__getstate__(), self.atla_collector
        )
        instance.__setstate__({"baml_options": {"collector": new_collectors}})
        return wrapped(*args, **kwargs)

    def _sync_stream_wrapper(
        self,
        wrapped: Callable[..., Any],
        instance: Any,
        args: tuple[Any, ...],
        kwargs: Mapping[str, Any],
    ) -> Any:
        """Wrap the BAML stream function."""
        with self.tracer.start_as_current_span(
            name="GenerateStreamSync",  # TODO: Add function name
            attributes={
                SpanAttributes.OPENINFERENCE_SPAN_KIND: (
                    OpenInferenceSpanKindValues.LLM.value
                ),
            },
            record_exception=False,
            set_status_on_exception=False,
        ) as span:
            try:
                for item in wrapped(*args, **kwargs):
                    yield item
            except Exception as exception:
                span.set_status(
                    trace_api.Status(trace_api.StatusCode.ERROR, str(exception))
                )
                span.record_exception(exception)
                raise

            span.set_status(trace_api.StatusCode.OK)

            if (
                self.atla_collector.last is not None
                and self.atla_collector.last.selected_call is not None
            ):
                if llm_request := self.atla_collector.last.selected_call.http_request:
                    request_body = llm_request.body.json()
                    span.set_attributes(
                        dict(self.llm_parser.parse_request_body(request_body))
                    )

            if isinstance(item, BaseModel):
                response_body = item.model_dump_json()
                span.set_attribute(
                    f"{SpanAttributes.LLM_OUTPUT_MESSAGES}.0.{MessageAttributes.MESSAGE_CONTENT}",
                    response_body,
                )
                span.set_attribute(
                    f"{SpanAttributes.LLM_OUTPUT_MESSAGES}.0.{MessageAttributes.MESSAGE_ROLE}",
                    "assistant",
                )

    def _sync_stream_final_response_wrapper(
        self,
        wrapped: Callable[..., Any],
        instance: Any,
        args: tuple[Any, ...],
        kwargs: Mapping[str, Any],
    ) -> Any:
        """Wrap the BAML stream function."""
        with self.tracer.start_as_current_span(
            name="GenerateStreamSync",  # TODO: Add function name
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
                self.atla_collector.last is not None
                and self.atla_collector.last.selected_call is not None
            ):
                if llm_request := self.atla_collector.last.selected_call.http_request:
                    request_body = llm_request.body.json()
                    span.set_attributes(
                        dict(self.llm_parser.parse_request_body(request_body))
                    )

            if isinstance(result, BaseModel):
                response_body = result.model_dump_json()
                span.set_attribute(
                    f"{SpanAttributes.LLM_OUTPUT_MESSAGES}.0.{MessageAttributes.MESSAGE_CONTENT}",
                    response_body,
                )
                span.set_attribute(
                    f"{SpanAttributes.LLM_OUTPUT_MESSAGES}.0.{MessageAttributes.MESSAGE_ROLE}",
                    "assistant",
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
        new_collectors = _get_updated_collectors(
            instance.__getstate__(), self.atla_collector
        )
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
                self.atla_collector.last is not None
                and self.atla_collector.last.selected_call is not None
            ):
                if llm_request := self.atla_collector.last.selected_call.http_request:
                    request_body = llm_request.body.json()
                    span.set_attributes(
                        dict(self.llm_parser.parse_request_body(request_body))
                    )

                if llm_response := self.atla_collector.last.selected_call.http_response:
                    response_body = llm_response.body.json()
                    span.set_attributes(
                        dict(self.llm_parser.parse_response_body(response_body))
                    )

        return result

    async def _async_stream_wrapper(
        self,
        wrapped: Callable[..., Any],
        instance: Any,
        args: tuple[Any, ...],
        kwargs: Mapping[str, Any],
    ) -> Any:
        """Wrap the BAML stream function."""
        with self.tracer.start_as_current_span(
            name="GenerateStreamAsync",  # TODO: Add function name
            attributes={
                SpanAttributes.OPENINFERENCE_SPAN_KIND: (
                    OpenInferenceSpanKindValues.LLM.value
                ),
            },
            record_exception=False,
            set_status_on_exception=False,
        ) as span:
            try:
                async for item in wrapped(*args, **kwargs):
                    yield item
            except Exception as exception:
                span.set_status(
                    trace_api.Status(trace_api.StatusCode.ERROR, str(exception))
                )
                span.record_exception(exception)
                raise

            span.set_status(trace_api.StatusCode.OK)

            if (
                self.atla_collector.last is not None
                and self.atla_collector.last.selected_call is not None
            ):
                if llm_request := self.atla_collector.last.selected_call.http_request:
                    request_body = llm_request.body.json()
                    span.set_attributes(
                        dict(self.llm_parser.parse_request_body(request_body))
                    )

            if isinstance(item, BaseModel):
                response_body = item.model_dump_json()
                span.set_attribute(
                    f"{SpanAttributes.LLM_OUTPUT_MESSAGES}.0.{MessageAttributes.MESSAGE_CONTENT}",
                    response_body,
                )
                span.set_attribute(
                    f"{SpanAttributes.LLM_OUTPUT_MESSAGES}.0.{MessageAttributes.MESSAGE_ROLE}",
                    "assistant",
                )

    async def _async_stream_final_response_wrapper(
        self,
        wrapped: Callable[..., Any],
        instance: Any,
        args: tuple[Any, ...],
        kwargs: Mapping[str, Any],
    ) -> Any:
        """Wrap the BAML stream function."""
        with self.tracer.start_as_current_span(
            name="GenerateStreamAsync",  # TODO: Add function name
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
                self.atla_collector.last is not None
                and self.atla_collector.last.selected_call is not None
            ):
                if llm_request := self.atla_collector.last.selected_call.http_request:
                    request_body = llm_request.body.json()
                    span.set_attributes(
                        dict(self.llm_parser.parse_request_body(request_body))
                    )

            if isinstance(result, BaseModel):
                response_body = result.model_dump_json()
                span.set_attribute(
                    f"{SpanAttributes.LLM_OUTPUT_MESSAGES}.0.{MessageAttributes.MESSAGE_CONTENT}",
                    response_body,
                )
                span.set_attribute(
                    f"{SpanAttributes.LLM_OUTPUT_MESSAGES}.0.{MessageAttributes.MESSAGE_ROLE}",
                    "assistant",
                )
        return result

    def instrumentation_dependencies(self) -> Collection[str]:
        """Return a list of python packages that the will be instrumented."""
        return ("baml-py",)

    def _instrument(self, **kwargs: Any) -> None:
        # Instrument the sync call function
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

        # Instrument the sync stream function
        self.original_create_stream_function_sync = getattr(
            import_module("baml_client.runtime").DoNotUseDirectlyCallManager,
            "create_sync_stream",
            None,
        )
        wrap_function_wrapper(
            module="baml_client.runtime",
            name="DoNotUseDirectlyCallManager.create_sync_stream",
            wrapper=self._create_stream_wrapper,
        )
        self.original_stream_function_sync = getattr(
            import_module("baml_py.stream").BamlSyncStream,
            "__iter__",
            None,
        )
        wrap_function_wrapper(
            module="baml_py.stream",
            name="BamlSyncStream.__iter__",
            wrapper=self._sync_stream_wrapper,
        )
        self.original_stream_final_response_function_sync = getattr(
            import_module("baml_py.stream").BamlSyncStream,
            "get_final_response",
            None,
        )
        wrap_function_wrapper(
            module="baml_py.stream",
            name="BamlSyncStream.get_final_response",
            wrapper=self._sync_stream_final_response_wrapper,
        )

        # Instrument the async call function
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

        # Instrument the async stream function
        self.original_create_stream_function_async = getattr(
            import_module("baml_client.runtime").DoNotUseDirectlyCallManager,
            "create_async_stream",
            None,
        )
        wrap_function_wrapper(
            module="baml_client.runtime",
            name="DoNotUseDirectlyCallManager.create_async_stream",
            wrapper=self._create_stream_wrapper,
        )
        self.original_stream_function_async = getattr(
            import_module("baml_py.stream").BamlStream,
            "__aiter__",
            None,
        )
        wrap_function_wrapper(
            module="baml_py.stream",
            name="BamlStream.__aiter__",
            wrapper=self._async_stream_wrapper,
        )
        self.original_stream_final_response_function_async = getattr(
            import_module("baml_py.stream").BamlStream,
            "get_final_response",
            None,
        )
        wrap_function_wrapper(
            module="baml_py.stream",
            name="BamlStream.get_final_response",
            wrapper=self._async_stream_final_response_wrapper,
        )

    def _uninstrument(self, **kwargs: Any) -> None:
        # TODO: Remove atla collector from CallManager state

        if self.original_call_function_sync is not None:
            runtime_module = import_module("baml_client.runtime")
            runtime_module.DoNotUseDirectlyCallManager.call_function_sync = (
                self.original_call_function_sync
            )
            self.original_call_function_sync = None

        if self.original_create_stream_function_sync is not None:
            runtime_module = import_module("baml_client.runtime")
            runtime_module.DoNotUseDirectlyCallManager.create_sync_stream = (
                self.original_create_stream_function_sync
            )
            self.original_create_stream_function_sync = None
        if self.original_stream_function_sync is not None:
            stream_module = import_module("baml_py.stream")
            stream_module.BamlSyncStream.__iter__ = self.original_stream_function_sync
            self.original_stream_function_sync = None
        if self.original_stream_final_response_function_sync is not None:
            stream_module = import_module("baml_py.stream")
            stream_module.BamlSyncStream.get_final_response = (
                self.original_stream_final_response_function_sync
            )
            self.original_stream_final_response_function_sync = None

        if self.original_call_function_async is not None:
            runtime_module = import_module("baml_client.runtime")
            runtime_module.DoNotUseDirectlyCallManager.call_function_async = (
                self.original_call_function_async
            )
            self.original_call_function_async = None

        if self.original_create_stream_function_async is not None:
            runtime_module = import_module("baml_client.runtime")
            runtime_module.DoNotUseDirectlyCallManager.create_async_stream = (
                self.original_create_stream_function_async
            )
            self.original_create_stream_function_async = None
        if self.original_stream_function_async is not None:
            stream_module = import_module("baml_py.stream")
            stream_module.BamlStream.__aiter__ = self.original_stream_function_async
            self.original_stream_function_async = None
        if self.original_stream_final_response_function_async is not None:
            stream_module = import_module("baml_py.stream")
            stream_module.BamlStream.get_final_response = (
                self.original_stream_final_response_function_async
            )
            self.original_stream_final_response_function_async = None
