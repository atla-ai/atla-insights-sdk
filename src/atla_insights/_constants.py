"""Constants for the atla_insights package."""

from typing import Literal

DEFAULT_OTEL_ATTRIBUTE_COUNT_LIMIT = 4096

MAX_METADATA_FIELDS = 25
MAX_METADATA_KEY_CHARS = 40
MAX_METADATA_VALUE_CHARS = 100

METADATA_MARK = "atla.metadata"
SUCCESS_MARK = "atla.mark.success"

LOGFIRE_OTEL_TRACES_ENDPOINT = "https://logfire-eu.pydantic.dev/v1/traces"

SUPPORTED_LLM_PROVIDER = Literal["anthropic", "google-genai", "litellm", "openai"]
