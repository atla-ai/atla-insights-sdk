"""Google GenAI instrumentation."""

import json
from typing import Iterable, Iterator, Tuple

from openinference.semconv.trace import MessageAttributes, ToolCallAttributes
from opentelemetry.util.types import AttributeValue

try:
    from openinference.instrumentation.google_genai import GoogleGenAIInstrumentor
    from openinference.instrumentation.google_genai._response_attributes_extractor import (  # noqa
        _ResponseAttributesExtractor,
    )
except ImportError as e:
    raise ImportError(
        "Google GenAI instrumentation needs to be installed. "
        "Please install it via `pip install atla-insights[google-genai]`."
    ) from e


def _get_attributes_from_content_parts(
    self: _ResponseAttributesExtractor,
    content_parts: Iterable[object],
) -> Iterator[Tuple[str, AttributeValue]]:
    """Custom response attribute override to include structured tool call information.

    TODO(mathias): Add support for built-in, Google-native tools (e.g. search).

    :param self (_ResponseAttributesExtractor): Original response attributes extractor.
    :param content_parts (Iterable[object]): Content parts to extract from.
    """
    function_call_idx = 0
    for part in content_parts:
        if text := getattr(part, "text", None):
            yield MessageAttributes.MESSAGE_CONTENT, text
        if function_call := getattr(part, "function_call", None):
            function_call_prefix = (
                f"{MessageAttributes.MESSAGE_TOOL_CALLS}.{function_call_idx}"
            )
            if function_name := getattr(function_call, "name", None):
                yield (
                    ".".join(
                        [function_call_prefix, ToolCallAttributes.TOOL_CALL_FUNCTION_NAME]
                    ),
                    function_name,
                )
            if function_id := getattr(function_call, "id", None):
                yield (
                    ".".join([function_call_prefix, ToolCallAttributes.TOOL_CALL_ID]),
                    function_id,
                )
            if function_args := getattr(function_call, "args", None):
                function_args_json = json.dumps(function_args)
            else:
                function_args_json = ""
            yield (
                ".".join(
                    [
                        function_call_prefix,
                        ToolCallAttributes.TOOL_CALL_FUNCTION_ARGUMENTS_JSON,
                    ]
                ),
                function_args_json,
            )

            function_call_idx += 1


class AtlaGoogleGenAIInstrumentor(GoogleGenAIInstrumentor):
    """Atla Google GenAI instrumentor class."""

    def _instrument(self, **kwargs) -> None:
        _ResponseAttributesExtractor._get_attributes_from_content_parts = (  # type: ignore[method-assign]
            _get_attributes_from_content_parts
        )
        super()._instrument(**kwargs)
