"""Span helper functions (lower-level interface)."""

import json
from contextlib import contextmanager
from typing import Any, Iterator, Mapping, Optional, Sequence, cast

from openai.types.chat import (
    ChatCompletionAssistantMessageParam,
    ChatCompletionContentPartTextParam,
    ChatCompletionMessageParam,
    ChatCompletionMessageToolCallParam,
    ChatCompletionToolParam,
)
from openai.types.chat.chat_completion_assistant_message_param import FunctionCall
from openinference.semconv.trace import (
    MessageAttributes,
    OpenInferenceMimeTypeValues,
    OpenInferenceSpanKindValues,
    SpanAttributes,
    ToolAttributes,
    ToolCallAttributes,
)
from opentelemetry.trace import Span

from atla_insights.main import ATLA_INSTANCE


class AtlaSpan:
    """Atla span."""

    def __init__(self, span: Span):
        """Initialize the Atla span.

        :param span (Span): The underlying span.
        """
        self._span = span

    def __getattr__(self, name: str) -> Any:
        """Get an attribute from the underlying span.

        :param name (str): The name of the attribute to get.
        :return (Any): The value of the attribute.
        """
        return getattr(self._span, name)

    def _record_messages(
        self,
        prefix: str,
        messages: Sequence[ChatCompletionMessageParam],
    ) -> None:
        """Record OpenAI-compatible messages.

        :param prefix (str): The prefix to use for the message attributes.
        :param messages (Sequence[ChatCompletionMessageParam]): The messages to record.
        """
        for message_idx, message in enumerate(messages):
            message_prefix = f"{prefix}.{message_idx}"

            self._span.set_attribute(
                f"{message_prefix}.{MessageAttributes.MESSAGE_ROLE}", message["role"]
            )

            if content := message.get("content"):
                if isinstance(content, str):
                    self._span.set_attribute(
                        f"{message_prefix}.{MessageAttributes.MESSAGE_CONTENT}", content
                    )
                elif isinstance(content, list):
                    for content_part in content:
                        if not isinstance(content_part, Mapping):
                            continue

                        if content_part.get("type") == "text":
                            content_part = cast(
                                ChatCompletionContentPartTextParam, content_part
                            )
                            text_content = content_part["text"]
                            self._span.set_attribute(
                                f"{message_prefix}.{MessageAttributes.MESSAGE_CONTENT}",
                                text_content,
                            )

            if tool_call_id := message.get("tool_call_id"):
                self._span.set_attribute(
                    f"{message_prefix}.{MessageAttributes.MESSAGE_TOOL_CALL_ID}",
                    str(tool_call_id),
                )

            if name := message.get("name"):
                self._span.set_attribute(
                    f"{message_prefix}.{MessageAttributes.MESSAGE_NAME}", str(name)
                )

            if tool_calls := message.get("tool_calls"):
                tool_calls = cast(list[ChatCompletionMessageToolCallParam], tool_calls)

                tool_calls_prefix = (
                    f"{message_prefix}.{MessageAttributes.MESSAGE_TOOL_CALLS}"
                )

                for tool_call_idx, tool_call in enumerate(tool_calls):
                    tool_call_prefix = f"{tool_calls_prefix}.{tool_call_idx}"

                    self._span.set_attribute(
                        f"{tool_call_prefix}.{ToolCallAttributes.TOOL_CALL_ID}",
                        tool_call["id"],
                    )
                    self._span.set_attribute(
                        f"{tool_call_prefix}.{ToolCallAttributes.TOOL_CALL_FUNCTION_NAME}",
                        tool_call["function"]["name"],
                    )
                    self._span.set_attribute(
                        f"{tool_call_prefix}.{ToolCallAttributes.TOOL_CALL_FUNCTION_ARGUMENTS_JSON}",
                        tool_call["function"]["arguments"],
                    )

            if function_call := message.get("function_call"):
                function_call = cast(FunctionCall, function_call)

                self._span.set_attribute(
                    f"{message_prefix}.{MessageAttributes.MESSAGE_FUNCTION_CALL_NAME}",
                    function_call["name"],
                )
                self._span.set_attribute(
                    f"{message_prefix}.{MessageAttributes.MESSAGE_FUNCTION_CALL_ARGUMENTS_JSON}",
                    function_call["arguments"],
                )

    def _record_tools(
        self,
        prefix: str,
        tools: Sequence[ChatCompletionToolParam],
    ) -> None:
        """Record OpenAI-compatible tools.

        :param prefix (str): The prefix to use for the tool attributes.
        :param tools (Sequence[ChatCompletionToolParam]): The tools to record.
        """
        for tool_idx, tool in enumerate(tools):
            self._span.set_attribute(
                f"{prefix}.{tool_idx}.{ToolAttributes.TOOL_JSON_SCHEMA}", json.dumps(tool)
            )

    def record_generation(
        self,
        input_messages: list[ChatCompletionMessageParam],
        output_messages: list[ChatCompletionAssistantMessageParam],
        tools: Optional[list[ChatCompletionToolParam]] = None,
    ) -> None:
        """Manually record an LLM generation.

        This method is intended to be used to manually record LLM generations that cannot
        be picked up by built-in framework/provider instrumentation.

        All parameters are expected to be OpenAI-compatible.

        ```py
        from atla_insights.span import start_as_current_span

        with start_as_current_span("my-llm-generation") as span:
            span.record_generation(
                input_messages=[
                    {"role": "system", "content": "You are a helpful assistant."},
                    {"role": "user", "content": "What is the capital of France?"},
                    {"role": "assistant", "content": "The capital of France is Paris."},
                    {"role": "user", "content": "What is the capital of Germany?"},
                ],
                output_messages=[
                    {
                        "role": "assistant",
                        "tool_calls": [
                            {
                                "id": "1",
                                "function": {
                                    "name": "get_capital",
                                    "arguments": '{"country": "Germany"}',
                                },
                            }
                        ],
                    },
                ],
                tools=[
                    {
                        "type": "function",
                        "function": {
                            "name": "get_capital",
                            "parameters": {
                                "type": "object",
                                "description": "Get the capital of a country.",
                                "properties": {
                                    "country": {"type": "string"},
                                },
                            },
                        },
                    },
                ],
            )
        ```

        :param input_messages (list[ChatCompletionMessageParam]): The input messages
            passed to the LLM.
        :param output_messages (list[ChatCompletionAssistantMessageParam]): The output
            message(s) returned by the LLM.
        :param tools (Optional[list[ChatCompletionToolParam]]): All tools available to
            the LLM. Defaults to `None`.
        """
        self._span.set_attribute(
            SpanAttributes.OPENINFERENCE_SPAN_KIND, OpenInferenceSpanKindValues.LLM.value
        )

        # Record input messages
        self._span.set_attribute(SpanAttributes.INPUT_VALUE, str(input_messages))
        self._span.set_attribute(
            SpanAttributes.INPUT_MIME_TYPE, OpenInferenceMimeTypeValues.JSON.value
        )
        self._record_messages(SpanAttributes.LLM_INPUT_MESSAGES, input_messages)

        # Record output messages
        self._span.set_attribute(SpanAttributes.OUTPUT_VALUE, str(output_messages))
        self._span.set_attribute(
            SpanAttributes.OUTPUT_MIME_TYPE, OpenInferenceMimeTypeValues.JSON.value
        )
        self._record_messages(SpanAttributes.LLM_OUTPUT_MESSAGES, output_messages)

        # Record available tools
        if tools:
            self._record_tools(SpanAttributes.LLM_TOOLS, tools)


@contextmanager
def start_as_current_span(name: str) -> Iterator[AtlaSpan]:
    """Start a span as the current span.

    This function is intended to be used to manually record a span to attach LLM-related
    attributes to, which cannot be picked up by built-in framework/provider
    instrumentation.

    ```py
    from atla_insights.span import start_as_current_span

    with start_as_current_span("my-llm-generation") as span:
        span.record_generation(...)
    ```

    :param name (str): The name of the span.
    :return (Iterator[AtlaSpan]): An iterator that yields the Atla span to attach
        LLM-related attributes to.
    """
    tracer_provider = ATLA_INSTANCE.tracer_provider
    if tracer_provider is None:
        raise ValueError("Must first configure Atla Insights before using the span API.")

    tracer = tracer_provider.get_tracer("openinference.instrumentation.manual")
    with tracer.start_as_current_span(name) as span:
        yield AtlaSpan(span)
