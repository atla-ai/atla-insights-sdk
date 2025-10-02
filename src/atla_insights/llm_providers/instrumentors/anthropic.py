"""Anthropic instrumentation."""

from itertools import chain
from typing import Any, Callable, Iterator, Mapping, Tuple

import opentelemetry.context as context_api
from opentelemetry import trace as trace_api
from wrapt import ObjectProxy, wrap_function_wrapper

try:
    from openinference.instrumentation import get_attributes_from_context
    from openinference.instrumentation.anthropic import AnthropicInstrumentor
    from openinference.instrumentation.anthropic._stream import _MessagesStream
    from openinference.instrumentation.anthropic._with_span import _WithSpan
    from openinference.instrumentation.anthropic._wrappers import (
        _get_inputs,
        _get_invocation_parameters,
        _get_llm_input_messages,
        _get_llm_invocation_parameters,
        _get_llm_model_name_from_input,
        _get_llm_provider,
        _get_llm_span_kind,
        _get_llm_system,
        _get_llm_tools,
        _WithTracer,
    )
except ImportError as e:
    raise ImportError(
        "Anthropic instrumentation needs to be installed. "
        'Please install it via `pip install "atla-insights[anthropic]"`.'
    ) from e


class _AsyncMessagesStreamWrapper(_WithTracer):
    """Async wrapper for the pipeline processing.

    Captures all calls to the async pipeline.
    """

    def __call__(
        self,
        wrapped: Callable[..., Any],
        instance: Any,
        args: Tuple[Any, ...],
        kwargs: Mapping[str, Any],
    ) -> Any:
        if context_api.get_value(context_api._SUPPRESS_INSTRUMENTATION_KEY):
            return wrapped(*args, **kwargs)

        arguments = kwargs
        llm_input_messages = dict(arguments).pop("messages", None)
        invocation_parameters = _get_invocation_parameters(arguments)

        with self._start_as_current_span(
            span_name="AsyncMessagesStream",
            attributes=dict(
                chain(
                    get_attributes_from_context(),
                    _get_llm_model_name_from_input(arguments),
                    _get_llm_provider(),
                    _get_llm_system(),
                    _get_llm_span_kind(),
                    _get_llm_input_messages(llm_input_messages),
                    _get_llm_invocation_parameters(invocation_parameters),
                    _get_llm_tools(invocation_parameters),
                    _get_inputs(arguments),
                )
            ),
        ) as span:
            try:
                response = wrapped(*args, **kwargs)
            except Exception as exception:
                span.set_status(trace_api.Status(trace_api.StatusCode.ERROR))
                span.record_exception(exception)
                raise

            return _AsyncMessageStreamManager(response, span)


class _AsyncMessageStreamManager(ObjectProxy):  # type: ignore
    def __init__(
        self,
        manager: Any,  # MessageStreamManager
        with_span: _WithSpan,
    ) -> None:
        super().__init__(manager)
        self._self_with_span = with_span

    async def __aenter__(self) -> Iterator[str]:
        raw = await self.__wrapped__.__aenter__()
        return _MessagesStream(raw, self._self_with_span)

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        try:
            result = await self.__wrapped__.__aexit__(exc_type, exc_val, exc_tb)
        finally:
            # Ensure the span is finished when the async context manager exits
            self._self_with_span.finish_tracing()
        return result


class AtlaAnthropicInstrumentor(AnthropicInstrumentor):
    """Atla Anthropic instrumentor class."""

    name = "anthropic"

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        """Initialize the AtlaAnthropicInstrumentor."""
        super().__init__(*args, **kwargs)

        self.original_completions_create = None
        self.original_async_completions_create = None
        self.original_messages_create = None
        self.original_async_messages_create = None
        self.original_messages_stream = None
        self.original_async_messages_stream = None

    def _instrument(self, **kwargs) -> None:
        from anthropic.resources.messages import AsyncMessages

        super()._instrument(**kwargs)

        self.original_async_messages_stream = AsyncMessages.stream  # type: ignore[assignment]
        wrap_function_wrapper(
            module="anthropic.resources.messages",
            name="AsyncMessages.stream",
            wrapper=_AsyncMessagesStreamWrapper(tracer=self._tracer),
        )

    def _uninstrument(self, **kwargs) -> None:
        from anthropic.resources.messages import AsyncMessages

        super()._uninstrument(**kwargs)

        if self.original_async_messages_stream is not None:
            AsyncMessages.stream = self.original_async_messages_stream

        self.original_completions_create = None
        self.original_async_completions_create = None
        self.original_messages_create = None
        self.original_async_messages_create = None
        self.original_messages_stream = None
        self.original_async_messages_stream = None
