"""Constants for the atla_insights package."""

from typing import Literal, Sequence, Union

DEFAULT_OTEL_ATTRIBUTE_COUNT_LIMIT = 4096

MAX_METADATA_FIELDS = 25
MAX_METADATA_KEY_CHARS = 40
MAX_METADATA_VALUE_CHARS = 100

OTEL_NAMESPACE = "atla"

METADATA_MARK = f"{OTEL_NAMESPACE}.metadata"
SUCCESS_MARK = f"{OTEL_NAMESPACE}.mark.success"

OTEL_MODULE_NAME = "atla_insights"
OTEL_TRACES_ENDPOINT = "https://logfire-eu.pydantic.dev/v1/traces"

SUPPORTED_LLM_FORMAT = Literal["anthropic"]
SUPPORTED_LLM_PROVIDER = Literal["anthropic", "google-genai", "litellm", "openai"]
LLM_PROVIDER_TYPE = Union[Sequence[SUPPORTED_LLM_PROVIDER], SUPPORTED_LLM_PROVIDER]
