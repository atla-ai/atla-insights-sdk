"""Constants for the atla_insights package."""

from typing import Literal, Sequence, Union

DEFAULT_OTEL_ATTRIBUTE_COUNT_LIMIT = 4096

MAX_METADATA_FIELDS = 25
MAX_METADATA_KEY_CHARS = 40
MAX_METADATA_VALUE_CHARS = 100

METADATA_MARK = "atla.metadata"
SUCCESS_MARK = "atla.mark.success"

OTEL_MODULE_NAME = "atla_insights"
OTEL_TRACES_ENDPOINT = "https://logfire-eu.pydantic.dev/v1/traces"

SUPPORTED_LLM_PROVIDER = Literal["anthropic", "google-genai", "litellm", "openai"]
LLM_PROVIDER_TYPE = Union[Sequence[SUPPORTED_LLM_PROVIDER], SUPPORTED_LLM_PROVIDER]
