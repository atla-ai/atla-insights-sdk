"""Parsers for the Anthropic LLM."""

import logging
from typing import Any, Generator

try:
    from anthropic.types.message import Message
    from openinference.instrumentation.anthropic._wrappers import (
        _get_llm_input_messages,
        _get_llm_tools,
        _get_output_messages,
    )
except ImportError as e:
    raise ImportError(
        "Anthropic instrumentation needs to be installed. "
        'Please install it via `pip install "atla-insights[anthropic]"`.'
    ) from e

from openinference.semconv.trace import (
    OpenInferenceLLMProviderValues,
    OpenInferenceLLMSystemValues,
    OpenInferenceMimeTypeValues,
    SpanAttributes,
)

from atla_insights.parsers.base import BaseParser

logger = logging.getLogger(__name__)


class AnthropicParser(BaseParser):
    """Parser for Anthropic's native API format."""

    name = "anthropic"

    def parse_request_body(
        self, request: dict[str, Any]
    ) -> Generator[tuple[str, Any], None, None]:
        """Parse the Anthropic request."""
        yield SpanAttributes.INPUT_VALUE, str(request)
        yield SpanAttributes.INPUT_MIME_TYPE, OpenInferenceMimeTypeValues.JSON.value

        yield SpanAttributes.LLM_PROVIDER, OpenInferenceLLMProviderValues.ANTHROPIC.value
        yield SpanAttributes.LLM_SYSTEM, OpenInferenceLLMSystemValues.ANTHROPIC.value

        if model := request.get("model"):
            yield SpanAttributes.LLM_MODEL_NAME, model

        if messages := request.get("messages"):
            yield from _get_llm_input_messages(messages)

        if tools := request.get("tools"):
            yield from _get_llm_tools(tools)

    def parse_response_body(
        self, response: dict[str, Any]
    ) -> Generator[tuple[str, Any], None, None]:
        """Parse the Anthropic response."""
        yield SpanAttributes.OUTPUT_VALUE, str(response)
        yield SpanAttributes.OUTPUT_MIME_TYPE, OpenInferenceMimeTypeValues.JSON.value

        try:
            message = Message(**response)
        except Exception as e:
            logger.error(f"Failed to parse Anthropic response: {e}")
            return

        yield from _get_output_messages(message)
