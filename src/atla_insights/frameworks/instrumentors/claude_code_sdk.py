"""Claude Code SDK instrumentor."""

import json
import logging
from contextvars import ContextVar
from typing import Any, Callable, Collection, Generator, Mapping, Optional, Sequence

from opentelemetry.instrumentation.instrumentor import (  # type: ignore[attr-defined]
    BaseInstrumentor,
)
from opentelemetry.trace import Status, StatusCode, Tracer
from wrapt import wrap_function_wrapper

try:
    from claude_code_sdk._internal.transport.subprocess_cli import (
        SubprocessCLITransport,
    )
except ImportError as e:
    raise ImportError(
        "Claude Code SDK instrumentation needs to be installed. "
        'Please install it via `pip install "atla-insights[claude-code-sdk]"`.'
    ) from e

from openinference.semconv.trace import (
    MessageAttributes,
    OpenInferenceMimeTypeValues,
    OpenInferenceSpanKindValues,
    SpanAttributes,
    ToolAttributes,
    ToolCallAttributes,
)

from atla_insights.constants import OTEL_MODULE_NAME

logger = logging.getLogger(OTEL_MODULE_NAME)


def _get_input_messages(
    messages: list[dict[str, Any]],
) -> Generator[tuple[str, Any], None, None]:
    """Get the input messages."""
    for idx, message in enumerate(messages):
        if not isinstance(message, dict):
            continue

        if role := message.get("role"):
            yield (
                f"{SpanAttributes.LLM_INPUT_MESSAGES}.{idx}.{MessageAttributes.MESSAGE_ROLE}",
                role,
            )
        if content := message.get("content"):
            yield (
                f"{SpanAttributes.LLM_INPUT_MESSAGES}.{idx}.{MessageAttributes.MESSAGE_CONTENT}",
                content,
            )


def _get_output_messages(
    message: dict[str, Any], message_idx: int
) -> Generator[tuple[str, Any], None, None]:
    """Get the output messages."""
    if output_message := message.get("message"):
        if role := output_message.get("role"):
            yield (
                f"{SpanAttributes.LLM_OUTPUT_MESSAGES}.{message_idx}.{MessageAttributes.MESSAGE_ROLE}",
                role,
            )
        if content := output_message.get("content"):
            if isinstance(content, Sequence):
                block_idx = 0
                for block in content:
                    if isinstance(block, dict):
                        if block.get("type") == "text":
                            yield (
                                f"{SpanAttributes.LLM_OUTPUT_MESSAGES}.{message_idx}.{MessageAttributes.MESSAGE_CONTENT}",
                                block["text"],
                            )
                        elif block.get("type") == "tool_use":
                            yield (
                                f"{SpanAttributes.LLM_OUTPUT_MESSAGES}.{message_idx}.{MessageAttributes.MESSAGE_TOOL_CALLS}.{block_idx}.{ToolCallAttributes.TOOL_CALL_ID}",
                                block["id"],
                            )
                            yield (
                                f"{SpanAttributes.LLM_OUTPUT_MESSAGES}.{message_idx}.{MessageAttributes.MESSAGE_TOOL_CALLS}.{block_idx}.{ToolCallAttributes.TOOL_CALL_FUNCTION_NAME}",
                                block["name"],
                            )
                            yield (
                                f"{SpanAttributes.LLM_OUTPUT_MESSAGES}.{message_idx}.{MessageAttributes.MESSAGE_TOOL_CALLS}.{block_idx}.{ToolCallAttributes.TOOL_CALL_FUNCTION_ARGUMENTS_JSON}",
                                json.dumps(block["input"]),
                            )
                        elif block.get("type") == "tool_result":
                            yield (
                                f"{SpanAttributes.LLM_OUTPUT_MESSAGES}.{message_idx}.{MessageAttributes.MESSAGE_CONTENT}",
                                block["content"],
                            )
                    block_idx += 1


def _get_llm_tools(
    message: dict[str, Any],
) -> Generator[tuple[str, Any], None, None]:
    """Get the output messages."""
    if tools := message.get("tools"):
        for idx, tool in enumerate(tools):
            tool_json = {"type": "function", "function": {"name": tool}}
            yield (
                f"{SpanAttributes.LLM_TOOLS}.{idx}.{ToolAttributes.TOOL_JSON_SCHEMA}",
                json.dumps(tool_json),
            )


def _get_llm_attributes(
    message: dict[str, Any],
) -> Generator[tuple[str, Any], None, None]:
    """Get the output messages."""
    if model := message.get("model"):
        yield SpanAttributes.LLM_MODEL_NAME, model


class AtlaClaudeCodeSdkInstrumentor(BaseInstrumentor):
    """Atla Claude Code SDK instrumentor class."""

    name = "claude-code-sdk"

    def __init__(self, tracer: Tracer) -> None:
        """Initialize the Atla Claude Code SDK instrumentor."""
        super().__init__()
        self.tracer = tracer

        self._input_attributes: ContextVar[Optional[Mapping[str, Any]]] = ContextVar(
            "input_attributes", default=None
        )

        self._original_send_request = None
        self._original_receive_messages = None

    def instrumentation_dependencies(self) -> Collection[str]:
        """Return the instrumentation dependencies."""
        return ("claude_code_sdk",)

    async def _wrap_send_request(
        self,
        wrapped: Callable[..., Any],
        instance: Any,
        args: tuple[Any, ...],
        kwargs: Mapping[str, Any],
    ) -> Any:
        """Wrap send_request to start a span."""
        if args and isinstance(args, Sequence) and isinstance(args[0], list):
            messages: list[Any] = args[0]

            parsed_messages = []
            for message in messages:
                parsed_message = (
                    message["message"]
                    if isinstance(message, dict)
                    else {"role": "user", "content": str(message)}
                )
                parsed_messages.append(parsed_message)

        self._input_attributes.set(
            {
                SpanAttributes.LLM_PROVIDER: "anthropic",
                SpanAttributes.INPUT_MIME_TYPE: OpenInferenceMimeTypeValues.JSON.value,
                SpanAttributes.INPUT_VALUE: json.dumps(args),
                SpanAttributes.OPENINFERENCE_SPAN_KIND: (
                    OpenInferenceSpanKindValues.LLM.value
                ),
                **dict(_get_input_messages(parsed_messages)),
            }
        )
        return await wrapped(*args, **kwargs)

    async def _wrap_receive_messages(
        self,
        wrapped: Callable[..., Any],
        instance: Any,
        args: tuple[Any, ...],
        kwargs: Mapping[str, Any],
    ) -> Any:
        """Wrap receive_messages to continue the span until generator is consumed."""
        span = self.tracer.start_span(
            name="Claude Code SDK Response",
            attributes=self._input_attributes.get(),
            record_exception=False,
            set_status_on_exception=False,
        )
        self._input_attributes.set(None)

        try:
            message_idx = 0
            async for message in wrapped(*args, **kwargs):
                message_attributes = {}
                if message_idx == 0:
                    message_attributes.update(
                        {
                            **dict(_get_llm_tools(message)),
                            **dict(_get_llm_attributes(message)),
                        }
                    )
                message_attributes.update(
                    {
                        **dict(_get_output_messages(message, message_idx)),
                    }
                )
                span.set_attributes(message_attributes)

                yield message

                message_idx += 1
                span.set_status(Status(StatusCode.OK))
        except Exception as e:
            span.record_exception(e)
            span.set_status(Status(StatusCode.ERROR))
            raise
        finally:
            span.end()

    def _instrument(self, **kwargs) -> None:
        """Instrument Claude Code SDK transport methods."""
        self._original_send_request = SubprocessCLITransport.send_request  # type: ignore[assignment]
        wrap_function_wrapper(
            "claude_code_sdk._internal.transport.subprocess_cli",
            "SubprocessCLITransport.send_request",
            self._wrap_send_request,
        )

        self._original_receive_messages = SubprocessCLITransport.receive_messages  # type: ignore[assignment]
        wrap_function_wrapper(
            "claude_code_sdk._internal.transport.subprocess_cli",
            "SubprocessCLITransport.receive_messages",
            self._wrap_receive_messages,
        )

    def _uninstrument(self, **kwargs) -> None:
        """Uninstrument Claude Code SDK."""
        if self._original_send_request is not None:
            SubprocessCLITransport.send_request = self._original_send_request
            self._original_send_request = None

        if self._original_receive_messages is not None:
            SubprocessCLITransport.receive_messages = self._original_receive_messages
            self._original_receive_messages = None
