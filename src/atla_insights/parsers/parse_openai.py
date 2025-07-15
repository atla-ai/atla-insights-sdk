"""Parsers for the OpenAI LLM."""

import logging
from typing import Any, Generator, Literal

try:
    from openinference.instrumentation.openai._request_attributes_extractor import (
        _RequestAttributesExtractor,
    )
    from openinference.instrumentation.openai._response_attributes_extractor import (
        _ResponseAttributesExtractor,
    )
except ImportError as e:
    raise ImportError(
        "OpenAI instrumentation needs to be installed. "
        'Please install it via `pip install "atla-insights[openai]"`.'
    ) from e

import openai
from openai.types.chat import ChatCompletion
from openai.types.responses import Response
from openinference.semconv.trace import (
    OpenInferenceLLMProviderValues,
    OpenInferenceLLMSystemValues,
    OpenInferenceMimeTypeValues,
    SpanAttributes,
)

from atla_insights.parsers.base import BaseParser

logger = logging.getLogger(__name__)


class OpenAIChatCompletionParser(BaseParser):
    """Parser for OpenAI's chat completion API format."""

    name = "openai"

    def __init__(
        self,
        api_endpoint: Literal["chat_completions", "responses"] = "chat_completions",
    ) -> None:
        """Initialize the OpenAIParser."""
        super().__init__()
        self._request_attributes_extractor = _RequestAttributesExtractor(openai)
        self._response_attributes_extractor = _ResponseAttributesExtractor(openai)

        self.cast_to: type[ChatCompletion | Response]
        match api_endpoint:
            case "chat_completions":
                self.cast_to = ChatCompletion
            case "responses":
                self.cast_to = Response
            case _:
                raise ValueError(f"Invalid API endpoint: {api_endpoint}")

    def parse_request_body(
        self, request: dict[str, Any]
    ) -> Generator[tuple[str, Any], None, None]:
        """Parse the OpenAI request."""
        yield SpanAttributes.INPUT_VALUE, str(request)
        yield SpanAttributes.INPUT_MIME_TYPE, OpenInferenceMimeTypeValues.JSON.value

        yield SpanAttributes.LLM_PROVIDER, OpenInferenceLLMProviderValues.OPENAI.value
        yield SpanAttributes.LLM_SYSTEM, OpenInferenceLLMSystemValues.OPENAI.value

        if model := request.get("model"):
            yield SpanAttributes.LLM_MODEL_NAME, model

        yield from self._request_attributes_extractor.get_attributes_from_request(
            request_parameters=request,
            cast_to=self.cast_to,
        )

    def parse_response_body(
        self, response: dict[str, Any]
    ) -> Generator[tuple[str, Any], None, None]:
        """Parse the OpenAI response."""
        yield SpanAttributes.OUTPUT_VALUE, str(response)
        yield SpanAttributes.OUTPUT_MIME_TYPE, OpenInferenceMimeTypeValues.JSON.value

        try:
            parsed_response = self.cast_to.model_validate(response)
        except Exception as e:
            logger.error(f"Failed to parse OpenAI response: {e}")
            return

        yield from self._response_attributes_extractor.get_attributes_from_response(
            response=parsed_response,
            request_parameters={},  # unused for chat completions
        )
