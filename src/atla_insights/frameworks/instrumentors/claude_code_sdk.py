"""Claude Code SDK instrumentor."""

import json
import logging
from contextvars import ContextVar
from dataclasses import asdict
from typing import (
    Any,
    AsyncIterable,
    Callable,
    Collection,
    Generator,
    Mapping,
    Optional,
    Sequence,
    cast,
)

from opentelemetry.instrumentation.instrumentor import (  # type: ignore[attr-defined]
    BaseInstrumentor,
)
from opentelemetry.trace import Status, StatusCode, Tracer
from wrapt import wrap_function_wrapper

try:
    from claude_code_sdk._internal.client import InternalClient
    from claude_code_sdk._internal.transport.subprocess_cli import SubprocessCLITransport
    from claude_code_sdk.types import ClaudeCodeOptions
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


def _get_tool_result_presence(content: Any) -> bool:
    """Check if the message contains a tool_result block.

    This is needed to correctly mark role as "tool" when these messages are treated as
    inputs (Claude Code SDK may label them as "user").
    """
    if isinstance(content, Sequence):
        for block in content:
            if isinstance(block, dict) and block.get("type") == "tool_result":
                return True
    return False


def _get_input_messages(
    messages: list[dict[str, Any]], options: dict[str, Any]
) -> Generator[tuple[str, Any], None, None]:
    """Get the input messages."""
    start_idx = 0
    if system_prompt := options.get("system_prompt"):
        start_idx = 1
        if append_system_prompt := options.get("append_system_prompt"):
            system_prompt = f"{system_prompt}\n{append_system_prompt}"

        yield (
            f"{SpanAttributes.LLM_INPUT_MESSAGES}.{0}.{MessageAttributes.MESSAGE_ROLE}",
            "system",
        )
        yield (
            f"{SpanAttributes.LLM_INPUT_MESSAGES}.{0}.{MessageAttributes.MESSAGE_CONTENT}",
            system_prompt,
        )

    for idx, message in enumerate(messages, start=start_idx):
        if not isinstance(message, dict):
            continue

        content = message.get("content")
        has_tool_result = _get_tool_result_presence(content)
        if role := message.get("role"):
            yield (
                f"{SpanAttributes.LLM_INPUT_MESSAGES}.{idx}.{MessageAttributes.MESSAGE_ROLE}",
                ("tool" if has_tool_result else role),
            )
        if content:
            yield (
                f"{SpanAttributes.LLM_INPUT_MESSAGES}.{idx}.{MessageAttributes.MESSAGE_CONTENT}",
                content,
            )


def _get_output_message(
    message: dict[str, Any], message_idx: int, as_input: bool
) -> Generator[tuple[str, Any], None, None]:
    """Get the output message."""
    prefix = (
        SpanAttributes.LLM_INPUT_MESSAGES
        if as_input
        else SpanAttributes.LLM_OUTPUT_MESSAGES
    )
    if output_message := message.get("message"):
        content = output_message.get("content")
        has_tool_result = _get_tool_result_presence(content)
        if role := output_message.get("role"):
            yield (
                f"{prefix}.{message_idx}.{MessageAttributes.MESSAGE_ROLE}",
                ("tool" if (as_input and has_tool_result) else role),
            )
        if content:
            if isinstance(content, Sequence):
                block_idx = 0
                for block in content:
                    if isinstance(block, dict):
                        if block.get("type") == "text":
                            yield (
                                f"{prefix}.{message_idx}.{MessageAttributes.MESSAGE_CONTENT}",
                                block["text"],
                            )
                        elif block.get("type") == "tool_use":
                            yield (
                                f"{prefix}.{message_idx}.{MessageAttributes.MESSAGE_TOOL_CALLS}.{block_idx}.{ToolCallAttributes.TOOL_CALL_ID}",
                                block["id"],
                            )
                            yield (
                                f"{prefix}.{message_idx}.{MessageAttributes.MESSAGE_TOOL_CALLS}.{block_idx}.{ToolCallAttributes.TOOL_CALL_FUNCTION_NAME}",
                                block["name"],
                            )
                            yield (
                                f"{prefix}.{message_idx}.{MessageAttributes.MESSAGE_TOOL_CALLS}.{block_idx}.{ToolCallAttributes.TOOL_CALL_FUNCTION_ARGUMENTS_JSON}",
                                json.dumps(block["input"]),
                            )
                        elif block.get("type") == "tool_result":
                            yield (
                                f"{prefix}.{message_idx}.{MessageAttributes.MESSAGE_CONTENT}",
                                block["content"],
                            )
                        elif block.get("type") == "thinking":
                            yield (
                                f"{prefix}.{message_idx}.{MessageAttributes.MESSAGE_CONTENT}",
                                block["thinking"],
                            )
                    block_idx += 1


def _get_output_messages(
    messages: list[dict[str, Any]], num_inputs: int
) -> Generator[tuple[str, Any], None, None]:
    """Get the output messages."""
    if not messages:
        return

    last_assistant_idx = None
    for i, msg in enumerate(messages):
        if msg.get("type") == "assistant":
            last_assistant_idx = i

    if last_assistant_idx is not None:
        yield from _get_output_message(messages[last_assistant_idx], 0, as_input=False)
        messages = messages[:last_assistant_idx]

    if messages[0].get("type") == "system":
        num_inputs -= 1

    for message_idx, message in enumerate(messages, start=num_inputs):
        yield from _get_output_message(message, message_idx, as_input=True)


def _get_llm_tools(
    message: dict[str, Any], options: dict[str, Any]
) -> Generator[tuple[str, Any], None, None]:
    """Get the LLM tools."""
    if tools := message.get("tools"):
        tools = cast(list[str], tools)
        if mcp_tools := options.get("mcp_tools"):
            mcp_tools = cast(list[str], mcp_tools)
            tools.extend(
                [
                    mcp_tool if mcp_tool.startswith("mcp__") else f"mcp__{mcp_tool}"
                    for mcp_tool in mcp_tools
                ]
            )

        # TODO(mathias): Filter tools based on allowed_tools and disallowed_tools, while
        # accounting for Claude Code SDK's tool filtering logic (e.g. `Bash(rm*)`).

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
        self._num_inputs: ContextVar[int] = ContextVar("num_inputs", default=0)
        self._options: ContextVar[Optional[dict[str, Any]]] = ContextVar(
            "options", default=None
        )

        self._original_process_query = None
        self._original_send_request = None
        self._original_receive_messages = None

    def instrumentation_dependencies(self) -> Collection[str]:
        """Return the instrumentation dependencies."""
        return ("claude_code_sdk",)

    async def _wrap_process_query(
        self,
        wrapped: Callable[..., Any],
        instance: Any,
        args: tuple[Any, ...],
        kwargs: Mapping[str, Any],
    ) -> Any:
        """Wrap process_query to start a span."""
        prompt: Optional[str | AsyncIterable[dict[str, Any]]] = kwargs.get("prompt")
        options: Optional[ClaudeCodeOptions] = kwargs.get("options")

        parsed_messages: list[dict[str, Any]] = []
        if prompt is not None:
            if isinstance(prompt, str):
                parsed_messages.append({"role": "user", "content": prompt})
            else:
                async for message in prompt:
                    parsed_messages.append(message)

        if options is not None:
            self._options.set(asdict(options))

        num_inputs = len(parsed_messages)
        if options is not None and options.system_prompt is not None:
            num_inputs += 1
        self._num_inputs.set(num_inputs)

        self._input_attributes.set(
            {
                SpanAttributes.LLM_PROVIDER: "anthropic",
                SpanAttributes.INPUT_MIME_TYPE: OpenInferenceMimeTypeValues.JSON.value,
                SpanAttributes.INPUT_VALUE: json.dumps(
                    [*parsed_messages, self._options.get() or {}]
                ),
                SpanAttributes.OPENINFERENCE_SPAN_KIND: (
                    OpenInferenceSpanKindValues.LLM.value
                ),
                **dict(_get_input_messages(parsed_messages, self._options.get() or {})),
            }
        )
        async for message in wrapped(*args, **kwargs):
            yield message

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

        if options := getattr(instance, "_options", None):
            self._options.set(asdict(options))

        num_inputs = len(parsed_messages)
        if options := self._options.get():
            if options.get("system_prompt"):
                num_inputs += 1
        self._num_inputs.set(num_inputs)

        self._input_attributes.set(
            {
                SpanAttributes.LLM_PROVIDER: "anthropic",
                SpanAttributes.INPUT_MIME_TYPE: OpenInferenceMimeTypeValues.JSON.value,
                SpanAttributes.INPUT_VALUE: json.dumps(args),
                SpanAttributes.OPENINFERENCE_SPAN_KIND: (
                    OpenInferenceSpanKindValues.LLM.value
                ),
                **dict(_get_input_messages(parsed_messages, self._options.get() or {})),
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
        )
        options = self._options.get() or {}

        try:
            llm_tools: Optional[dict] = None
            llm_attributes: Optional[dict] = None

            messages = []
            async for message in wrapped(*args, **kwargs):
                messages.append(message)

                if llm_tools is None:
                    llm_tools = dict(_get_llm_tools(message, options))
                    span.set_attributes(llm_tools)
                if llm_attributes is None:
                    llm_attributes = dict(_get_llm_attributes(message))
                    span.set_attributes(llm_attributes)

                if isinstance(message, Mapping) and message.get("type") == "result":
                    output_message_attributes = dict(
                        _get_output_messages(messages, self._num_inputs.get())
                    )
                    span.set_attributes(output_message_attributes)
                    span.set_status(Status(StatusCode.OK))

                yield message

        except Exception as e:
            span.record_exception(e)
            span.set_status(Status(StatusCode.ERROR))
            raise
        finally:
            span.end()

    def _instrument(self, **kwargs) -> None:
        """Instrument Claude Code SDK transport methods."""
        self._original_process_query = InternalClient.process_query  # type: ignore[assignment]
        wrap_function_wrapper(
            "claude_code_sdk._internal.client",
            "InternalClient.process_query",
            self._wrap_process_query,
        )

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
        if self._original_process_query is not None:
            InternalClient.process_query = self._original_process_query
            self._original_process_query = None

        if self._original_send_request is not None:
            SubprocessCLITransport.send_request = self._original_send_request
            self._original_send_request = None

        if self._original_receive_messages is not None:
            SubprocessCLITransport.receive_messages = self._original_receive_messages
            self._original_receive_messages = None
