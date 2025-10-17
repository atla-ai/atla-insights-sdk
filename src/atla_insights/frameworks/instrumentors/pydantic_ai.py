"""Pydantic AI instrumentation."""

from importlib import import_module
from typing import Any, Collection, Optional

from wrapt import wrap_function_wrapper

try:
    from openinference.instrumentation.pydantic_ai import OpenInferenceSpanProcessor
    from openinference.instrumentation.pydantic_ai.semantic_conventions import (
        GenAIFunctionFields,
        GenAIMessageFields,
        GenAIMessagePartFields,
        GenAIMessagePartTypes,
        GenAIMessageRoles,
        GenAISystemInstructionsFields,
        GenAIToolCallFields,
        PydanticFinalResult,
    )
    from pydantic_ai import Agent, InstrumentationSettings
except ImportError as e:
    raise ImportError(
        "Pydantic AI instrumentation needs to be installed. "
        'Please install it via `pip install "atla-insights[pydantic-ai]"`.'
    ) from e

import json
from typing import Callable, Iterator, Mapping, Tuple

from openinference.semconv.trace import (
    MessageAttributes,
    SpanAttributes,
    ToolCallAttributes,
)
from opentelemetry.instrumentation.instrumentor import (  # type: ignore[attr-defined]
    BaseInstrumentor,
)
from opentelemetry.sdk.trace import ReadableSpan
from opentelemetry.semconv._incubating.attributes.gen_ai_attributes import (
    GEN_AI_INPUT_MESSAGES,
    GEN_AI_OUTPUT_MESSAGES,
    GEN_AI_SYSTEM_INSTRUCTIONS,
)

from atla_insights.main import ATLA_INSTANCE


def _atla_extract_from_gen_ai_messages(  # noqa: C901
    wrapped: Callable[..., Any],
    instance: Any,
    args: tuple[Any, Any, Any],
    kwargs: Mapping[str, Any],
) -> Iterator[Tuple[str, Any]]:
    """Extract OpenInference attributes from pydantic_ai v2 gen_ai messages format."""
    gen_ai_attrs = args[0]

    # Extract input messages and input value
    input_value = None
    if GEN_AI_INPUT_MESSAGES in gen_ai_attrs:
        input_messages_str = gen_ai_attrs[GEN_AI_INPUT_MESSAGES]
        if isinstance(input_messages_str, str):
            try:
                msg_index = 0
                # First try and get any system instructions & convert to system messages
                if GEN_AI_SYSTEM_INSTRUCTIONS in gen_ai_attrs:
                    system_instructions = json.loads(
                        gen_ai_attrs[GEN_AI_SYSTEM_INSTRUCTIONS]
                    )
                    if isinstance(system_instructions, list):
                        for system_instruction in system_instructions:
                            if (
                                GenAISystemInstructionsFields.TYPE in system_instruction
                                and GenAISystemInstructionsFields.CONTENT
                                in system_instruction
                            ):
                                yield (
                                    f"{SpanAttributes.LLM_INPUT_MESSAGES}.{msg_index}.{MessageAttributes.MESSAGE_ROLE}",
                                    GenAIMessageRoles.SYSTEM,
                                )
                                yield (
                                    f"{SpanAttributes.LLM_INPUT_MESSAGES}.{msg_index}.{MessageAttributes.MESSAGE_CONTENT}",
                                    system_instruction[
                                        GenAISystemInstructionsFields.CONTENT
                                    ],
                                )
                                msg_index += 1

                input_messages = json.loads(input_messages_str)
                if isinstance(input_messages, list):
                    for msg in input_messages:
                        if GenAIMessageFields.ROLE in msg:
                            yield (
                                f"{SpanAttributes.LLM_INPUT_MESSAGES}.{msg_index}.{MessageAttributes.MESSAGE_ROLE}",
                                msg[GenAIMessageFields.ROLE],
                            )

                        # Extract content from parts
                        if GenAIMessageFields.PARTS in msg and isinstance(
                            msg[GenAIMessageFields.PARTS], list
                        ):
                            tool_call_idx = 0
                            for part in msg[GenAIMessageFields.PARTS]:
                                if isinstance(part, dict):
                                    if (
                                        part.get(GenAIMessagePartFields.TYPE)
                                        == GenAIMessagePartTypes.TEXT
                                        and GenAIMessagePartFields.CONTENT in part
                                    ):
                                        yield (
                                            f"{SpanAttributes.LLM_INPUT_MESSAGES}.{msg_index}.{MessageAttributes.MESSAGE_CONTENT}",
                                            part[GenAIMessagePartFields.CONTENT],
                                        )

                                        # Set INPUT_VALUE for the last user message found
                                        if (
                                            msg.get(GenAIMessageFields.ROLE)
                                            == GenAIMessageRoles.USER
                                        ):
                                            input_value = part[
                                                GenAIMessagePartFields.CONTENT
                                            ]
                                    elif (
                                        part.get(GenAIMessagePartFields.TYPE)
                                        == GenAIMessagePartTypes.TOOL_CALL
                                    ):
                                        # Extract tool call information
                                        if GenAIFunctionFields.NAME in part:
                                            yield (
                                                f"{SpanAttributes.LLM_INPUT_MESSAGES}.{msg_index}.{MessageAttributes.MESSAGE_TOOL_CALLS}.{tool_call_idx}.{ToolCallAttributes.TOOL_CALL_FUNCTION_NAME}",
                                                part[GenAIFunctionFields.NAME],
                                            )
                                        if GenAIFunctionFields.ARGUMENTS in part:
                                            yield (
                                                f"{SpanAttributes.LLM_INPUT_MESSAGES}.{msg_index}.{MessageAttributes.MESSAGE_TOOL_CALLS}.{tool_call_idx}.{ToolCallAttributes.TOOL_CALL_FUNCTION_ARGUMENTS_JSON}",
                                                part[GenAIFunctionFields.ARGUMENTS],
                                            )
                                        if GenAIToolCallFields.ID in part:
                                            yield (
                                                f"{SpanAttributes.LLM_INPUT_MESSAGES}.{msg_index}.{MessageAttributes.MESSAGE_TOOL_CALLS}.{tool_call_idx}.{ToolCallAttributes.TOOL_CALL_ID}",
                                                part[GenAIToolCallFields.ID],
                                            )
                                        tool_call_idx += 1
                                    elif part.get(
                                        GenAIMessagePartFields.TYPE
                                    ) == "tool_call_response" and part.get("result"):
                                        yield (
                                            f"{SpanAttributes.LLM_INPUT_MESSAGES}.{msg_index}.{MessageAttributes.MESSAGE_ROLE}",
                                            "tool",
                                        )
                                        yield (
                                            f"{SpanAttributes.LLM_INPUT_MESSAGES}.{msg_index}.{MessageAttributes.MESSAGE_CONTENT}",
                                            str(part["result"]),
                                        )
                                        msg_index += 1
                        msg_index += 1
            except json.JSONDecodeError:
                pass
    if input_value is not None:
        yield SpanAttributes.INPUT_VALUE, input_value

    # Extract output messages
    output_value = None
    if GEN_AI_OUTPUT_MESSAGES in gen_ai_attrs:
        output_messages_str = gen_ai_attrs[GEN_AI_OUTPUT_MESSAGES]
        if isinstance(output_messages_str, str):
            try:
                output_messages = json.loads(output_messages_str)
                if isinstance(output_messages, list):
                    for index, msg in enumerate(output_messages):
                        if GenAIMessageFields.ROLE in msg:
                            yield (
                                f"{SpanAttributes.LLM_OUTPUT_MESSAGES}.{index}.{MessageAttributes.MESSAGE_ROLE}",
                                msg[GenAIMessageFields.ROLE],
                            )

                        # Extract content or tool calls from parts
                        if GenAIMessageFields.PARTS in msg and isinstance(
                            msg[GenAIMessageFields.PARTS], list
                        ):
                            tool_call_idx = 0
                            for part in msg[GenAIMessageFields.PARTS]:
                                if isinstance(part, dict):
                                    if (
                                        part.get(GenAIMessagePartFields.TYPE)
                                        == GenAIMessagePartTypes.TEXT
                                        and GenAIMessagePartFields.CONTENT in part
                                    ):
                                        yield (
                                            f"{SpanAttributes.LLM_OUTPUT_MESSAGES}.{index}.{MessageAttributes.MESSAGE_CONTENT}",
                                            part[GenAIMessagePartFields.CONTENT],
                                        )
                                        break
                                    elif (
                                        part.get(GenAIMessagePartFields.TYPE)
                                        == GenAIMessagePartTypes.TOOL_CALL
                                    ):
                                        # Extract tool call information
                                        if GenAIFunctionFields.NAME in part:
                                            yield (
                                                f"{SpanAttributes.LLM_OUTPUT_MESSAGES}.{index}.{MessageAttributes.MESSAGE_TOOL_CALLS}.{tool_call_idx}.{ToolCallAttributes.TOOL_CALL_FUNCTION_NAME}",
                                                part[GenAIFunctionFields.NAME],
                                            )
                                            if (
                                                part.get(GenAIFunctionFields.NAME)
                                                == PydanticFinalResult.FINAL_RESULT
                                            ):
                                                output_value = part[
                                                    GenAIFunctionFields.ARGUMENTS
                                                ]
                                        if GenAIFunctionFields.ARGUMENTS in part:
                                            yield (
                                                f"{SpanAttributes.LLM_OUTPUT_MESSAGES}.{index}.{MessageAttributes.MESSAGE_TOOL_CALLS}.{tool_call_idx}.{ToolCallAttributes.TOOL_CALL_FUNCTION_ARGUMENTS_JSON}",
                                                part[GenAIFunctionFields.ARGUMENTS],
                                            )
                                        if GenAIToolCallFields.ID in part:
                                            yield (
                                                f"{SpanAttributes.LLM_OUTPUT_MESSAGES}.{index}.{MessageAttributes.MESSAGE_TOOL_CALLS}.{tool_call_idx}.{ToolCallAttributes.TOOL_CALL_ID}",
                                                part[GenAIToolCallFields.ID],
                                            )
                                        tool_call_idx += 1
            except json.JSONDecodeError:
                pass
    if output_value is not None:
        yield SpanAttributes.OUTPUT_VALUE, output_value


class _AtlaOpenInferenceSpanProcessor(OpenInferenceSpanProcessor):
    """Atla extension on the OpenInference Pydantic AI span processor."""

    def on_end(self, span: ReadableSpan) -> None:
        if pydantic_ai_instrumentor.instrumentation_active:
            super().on_end(span)


class _PydanticAIInstrumentor(BaseInstrumentor):
    """Pydantic AI instrumentor class."""

    name = "pydantic-ai"

    def __init__(self) -> None:
        """Initialize instrumentor without any active instrumentation."""
        self.is_instrumented = False
        self.instrumentation_active = False

        self.original_instrument_default: Optional[InstrumentationSettings | bool] = None
        self._original_extract_from_gen_ai_messages = None

    def instrumentation_dependencies(self) -> Collection[str]:
        """Return a list of python packages that the will be instrumented."""
        return ("pydantic-ai",)

    def _instrument(self, **kwargs: Any) -> None:
        if ATLA_INSTANCE.tracer_provider is None:
            raise ValueError(
                "Attempting to instrument `pydantic-ai` before configuring Atla. "
                "Please run `configure()` before instrumenting."
            )

        # Set flag so that span processor starts processing Pydantic AI spans.
        self.instrumentation_active = True

        # Change default instrumentation behavior for all agents.
        self.original_instrument_default = Agent._instrument_default
        Agent.instrument_all(True)

        self._original_extract_from_gen_ai_messages = getattr(
            import_module(
                "openinference.instrumentation.pydantic_ai.semantic_conventions"
            ),
            "_extract_from_gen_ai_messages",
            None,
        )
        wrap_function_wrapper(
            "openinference.instrumentation.pydantic_ai.semantic_conventions",
            "_extract_from_gen_ai_messages",
            _atla_extract_from_gen_ai_messages,
        )

        # Ensure actual span processor only gets added once to the tracer provider.
        if not self.is_instrumented:
            self.is_instrumented = True
            ATLA_INSTANCE.tracer_provider._active_span_processor._span_processors = (
                _AtlaOpenInferenceSpanProcessor(),
                *ATLA_INSTANCE.tracer_provider._active_span_processor._span_processors,
            )

    def _uninstrument(self, **kwargs: Any) -> None:
        # Set flag so that span processor stops processing Pydantic AI spans.
        self.instrumentation_active = False

        # Change default instrumentation behavior for all agents.
        if self.original_instrument_default is not None:
            Agent.instrument_all(self.original_instrument_default)
            self.original_instrument_default = None

        if self._original_extract_from_gen_ai_messages is not None:
            semconv_module = import_module(
                "openinference.instrumentation.pydantic_ai.semantic_conventions"
            )
            semconv_module._extract_from_gen_ai_messages = (
                self._original_extract_from_gen_ai_messages
            )
            self._original_extract_from_gen_ai_messages = None


# Create stateful singleton instrumentor class.
pydantic_ai_instrumentor = _PydanticAIInstrumentor()
