"""Parsers for the Bedrock LLM provider."""

import logging
from typing import Any, Generator, Literal

try:
    from openinference.instrumentation import safe_json_dumps
    from openinference.instrumentation.bedrock import _get_attributes_from_message_param
    from openinference.instrumentation.bedrock.utils.anthropic import _attributes
except ImportError as e:
    raise ImportError(
        "Bedrock instrumentation needs to be installed. "
        'Please install it via `pip install "atla-insights[bedrock]"`.'
    ) from e

from openinference.semconv.trace import (
    OpenInferenceLLMProviderValues,
    OpenInferenceLLMSystemValues,
    OpenInferenceMimeTypeValues,
    SpanAttributes,
)

from atla_insights.parsers.base import BaseParser

logger = logging.getLogger(__name__)


class BedrockParser(BaseParser):
    """Parser for Bedrock's native API format."""

    name = "bedrock"

    def __init__(
        self,
        api_endpoint: Literal["converse", "invoke_model"] = "converse",
    ) -> None:
        """Initialize the BedrockParser."""
        super().__init__()
        self.api_endpoint = api_endpoint

    def _process_converse_request(
        self, request: dict[str, Any]
    ) -> Generator[tuple[str, Any], None, None]:
        """Process an AWS Bedrock converse endpoint request."""
        if model_id := request.get("modelId"):
            yield SpanAttributes.LLM_MODEL_NAME, model_id

        if inference_config := request.get("inferenceConfig"):
            invocation_parameters = safe_json_dumps(inference_config)
            yield SpanAttributes.LLM_INVOCATION_PARAMETERS, invocation_parameters

        aggregated_messages = []
        if system_prompts := request.get("system"):
            aggregated_messages.append(
                {
                    "role": "system",
                    "content": [
                        {
                            "text": " ".join(
                                prompt.get("text", "") for prompt in system_prompts
                            )
                        }
                    ],
                }
            )

        aggregated_messages.extend(request.get("messages", []))
        for idx, msg in enumerate(aggregated_messages):
            if not isinstance(msg, dict):
                # Only dictionaries supported for now
                continue
            for key, value in _get_attributes_from_message_param(msg):
                yield f"{SpanAttributes.LLM_INPUT_MESSAGES}.{idx}.{key}", value

        last_message = aggregated_messages[-1]
        if isinstance(last_message, dict) and (
            request_msg_content := last_message.get("content")
        ):
            request_msg_prompt = "\n".join(
                content_input.get("text", "")  # type: ignore[attr-defined]
                for content_input in request_msg_content
            ).strip("\n")
            yield SpanAttributes.INPUT_VALUE, request_msg_prompt

    def parse_request_body(
        self, request: dict[str, Any]
    ) -> Generator[tuple[str, Any], None, None]:
        """Parse the Anthropic request."""
        yield SpanAttributes.INPUT_VALUE, str(request)
        yield SpanAttributes.INPUT_MIME_TYPE, OpenInferenceMimeTypeValues.JSON.value

        yield SpanAttributes.LLM_PROVIDER, OpenInferenceLLMProviderValues.ANTHROPIC.value
        yield SpanAttributes.LLM_SYSTEM, OpenInferenceLLMSystemValues.ANTHROPIC.value

        match self.api_endpoint:
            case "invoke_model":
                if "body" and "modelId" in request:
                    yield from _attributes.get_llm_input_attributes(
                        request_body=request["body"], model_id=request["modelId"]
                    ).items()
            case "converse":
                yield from self._process_converse_request(request)

    def _process_converse_response(
        self, response: dict[str, Any]
    ) -> Generator[tuple[str, Any], None, None]:
        """Process an AWS Bedrock converse endpoint response."""
        if (
            (response_message := response.get("output", {}).get("message"))
            and (response_role := response_message.get("role"))
            and (response_content := response_message.get("content", []))
        ):
            # Currently only supports text-based data
            response_text = "\n".join(
                content_input.get("text", "") for content_input in response_content
            )
            yield SpanAttributes.OUTPUT_VALUE, response_text

            span_prefix = f"{SpanAttributes.LLM_OUTPUT_MESSAGES}.0"
            yield f"{span_prefix}.message.role", response_role
            yield f"{span_prefix}.message.content", response_text

        if usage := response.get("usage"):
            if input_token_count := usage.get("inputTokens"):
                yield SpanAttributes.LLM_TOKEN_COUNT_PROMPT, input_token_count
            if response_token_count := usage.get("outputTokens"):
                yield SpanAttributes.LLM_TOKEN_COUNT_COMPLETION, response_token_count
            if total_token_count := usage.get("totalTokens"):
                yield SpanAttributes.LLM_TOKEN_COUNT_TOTAL, total_token_count

    def parse_response_body(
        self, response: dict[str, Any]
    ) -> Generator[tuple[str, Any], None, None]:
        """Parse the Anthropic response."""
        yield SpanAttributes.OUTPUT_VALUE, str(response)
        yield SpanAttributes.OUTPUT_MIME_TYPE, OpenInferenceMimeTypeValues.JSON.value

        match self.api_endpoint:
            case "invoke_model":
                if body := response.get("body"):
                    yield from _attributes.get_llm_output_attributes(body).items()
            case "converse":
                yield from self._process_converse_response(response)
