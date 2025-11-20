"""ElevenLabs instrumentation."""

import logging
import warnings
from contextvars import ContextVar
from typing import Any, Callable, Collection, Mapping, Optional

try:
    from elevenlabs.conversational_ai.conversation import (
        AsyncConversation,
        Conversation,
    )
except ImportError as e:
    raise ImportError(
        "ElevenLabs instrumentation needs to be installed. "
        'Please install it via `pip install "atla-insights[elevenlabs]"`.'
    ) from e

from openinference.semconv.trace import (
    OpenInferenceMimeTypeValues,
    OpenInferenceSpanKindValues,
    SpanAttributes,
)
from opentelemetry.instrumentation.instrumentor import (  # type: ignore[attr-defined]
    BaseInstrumentor,
)
from opentelemetry.trace import Span, Status, StatusCode, Tracer
from wrapt import wrap_function_wrapper

from atla_insights.constants import OTEL_MODULE_NAME

logger = logging.getLogger(OTEL_MODULE_NAME)


class AtlaElevenLabsInstrumentor(BaseInstrumentor):
    """An instrumentor for `elevenlabs`."""

    name = "elevenlabs"

    def __init__(self, tracer: Tracer) -> None:
        """Initialize the AtlaElevenLabsInstrumentor."""
        super().__init__()

        self.tracer = tracer

        self._active_span: ContextVar[Optional[Span]] = ContextVar(
            "_active_span", default=None
        )

        self._original_start_session = None
        self._original_end_session = None

        self._original_async_start_session = None
        self._original_async_end_session = None

    def instrumentation_dependencies(self) -> Collection[str]:
        """Return the dependencies required by the instrumentor."""
        return ("elevenlabs",)

    def _wrap_start_session(
        self,
        wrapped: Callable[..., Any],
        instance: Any,
        args: tuple[Any, ...],
        kwargs: Mapping[str, Any],
    ) -> Any:
        # TODO: Because `end_session` is not guaranteed to be called and could only get
        # called after uninstrumentation, there is a possibility of spans remaining alive
        # indefinitely. There should be a cleanup function to guard against this.
        span = self.tracer.start_span(
            name="ElevenLabs Conversation",
            attributes={
                SpanAttributes.LLM_PROVIDER: "elevenlabs",
                SpanAttributes.INPUT_MIME_TYPE: OpenInferenceMimeTypeValues.JSON.value,
                SpanAttributes.OPENINFERENCE_SPAN_KIND: (
                    OpenInferenceSpanKindValues.LLM.value
                ),
            },
            record_exception=False,
        )
        self._active_span.set(span)

        try:
            return wrapped(*args, **kwargs)
        except Exception as e:
            self._active_span.set(None)

            span.record_exception(e)
            span.set_status(Status(StatusCode.ERROR))
            span.end()
            raise

    async def _async_wrap_start_session(
        self,
        wrapped: Callable[..., Any],
        instance: Any,
        args: tuple[Any, ...],
        kwargs: Mapping[str, Any],
    ) -> Any:
        # TODO: Because `end_session` is not guaranteed to be called and could only get
        # called after uninstrumentation, there is a possibility of spans remaining alive
        # indefinitely. There should be a cleanup function to guard against this.
        span = self.tracer.start_span(
            name="ElevenLabs Conversation",
            attributes={
                SpanAttributes.LLM_PROVIDER: "elevenlabs",
                SpanAttributes.INPUT_MIME_TYPE: OpenInferenceMimeTypeValues.JSON.value,
                SpanAttributes.OPENINFERENCE_SPAN_KIND: (
                    OpenInferenceSpanKindValues.LLM.value
                ),
            },
            record_exception=False,
        )
        self._active_span.set(span)

        try:
            return await wrapped(*args, **kwargs)
        except Exception as e:
            self._active_span.set(None)

            span.record_exception(e)
            span.set_status(Status(StatusCode.ERROR))
            span.end()
            raise

    def _wrap_end_session(
        self,
        wrapped: Callable[..., Any],
        instance: Any,
        args: tuple[Any, ...],
        kwargs: Mapping[str, Any],
    ) -> Any:
        if not (active_span := self._active_span.get()):
            return wrapped(*args, **kwargs)

        try:
            if conversation_id := getattr(instance, "_conversation_id", None):
                active_span.set_attribute("atla.audio.conversation_id", conversation_id)
            return wrapped(*args, **kwargs)
        except Exception as e:
            active_span.record_exception(e)
            active_span.set_status(Status(StatusCode.ERROR))
            raise
        finally:
            self._active_span.set(None)
            active_span.end()

    async def _async_wrap_end_session(
        self,
        wrapped: Callable[..., Any],
        instance: Any,
        args: tuple[Any, ...],
        kwargs: Mapping[str, Any],
    ) -> Any:
        if not (active_span := self._active_span.get()):
            return await wrapped(*args, **kwargs)

        try:
            if conversation_id := getattr(instance, "_conversation_id", None):
                active_span.set_attribute("atla.audio.conversation_id", conversation_id)
            return await wrapped(*args, **kwargs)
        except Exception as e:
            active_span.record_exception(e)
            active_span.set_status(Status(StatusCode.ERROR))
            raise
        finally:
            self._active_span.set(None)
            active_span.end()

    def _instrument(self, **kwargs: Any) -> None:
        self._original_start_session = Conversation.start_session  # type: ignore[assignment]
        wrap_function_wrapper(
            module="elevenlabs.conversational_ai.conversation",
            name="Conversation.start_session",
            wrapper=self._wrap_start_session,
        )

        self._original_end_session = Conversation.end_session  # type: ignore[assignment]
        wrap_function_wrapper(
            module="elevenlabs.conversational_ai.conversation",
            name="Conversation.end_session",
            wrapper=self._wrap_end_session,
        )

        self._original_async_start_session = AsyncConversation.start_session  # type: ignore[assignment]
        wrap_function_wrapper(
            module="elevenlabs.conversational_ai.conversation",
            name="AsyncConversation.start_session",
            wrapper=self._async_wrap_start_session,
        )

        self._original_async_end_session = AsyncConversation.end_session  # type: ignore[assignment]
        wrap_function_wrapper(
            module="elevenlabs.conversational_ai.conversation",
            name="AsyncConversation.end_session",
            wrapper=self._async_wrap_end_session,
        )

    def _uninstrument(self, **kwargs: Any) -> None:
        if active_span := self._active_span.get():
            warnings.warn(
                "Uninstrumenting ElevenLabs while a span is active is not recommended! "
                "Please make sure to call `end_session` within the instrumentation "
                "context to avoid telemetry data loss",
                stacklevel=1,
            )
            self._active_span.set(None)
            active_span.end()

        if self._original_start_session is not None:
            Conversation.start_session = self._original_start_session
            self._original_start_session = None

        if self._original_end_session is not None:
            Conversation.end_session = self._original_end_session
            self._original_end_session = None

        if self._original_async_start_session is not None:
            AsyncConversation.start_session = self._original_async_start_session
            self._original_async_start_session = None

        if self._original_async_end_session is not None:
            AsyncConversation.end_session = self._original_async_end_session
            self._original_async_end_session = None
