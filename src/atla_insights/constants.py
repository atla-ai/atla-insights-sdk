"""Constants for the atla_insights package."""

import importlib.metadata
import json
from importlib.metadata import distributions
from typing import Literal, Sequence, Union

__version__ = importlib.metadata.version("atla-insights")

LIB_VERSIONS = json.dumps(
    {
        distribution.name: distribution.version
        for distribution in distributions()
        if distribution.name.startswith("openinference")
        or distribution.name.startswith("langchain")
        or distribution.name
        in [
            "agno",
            "anthropic",
            "baml-py",
            "boto3",
            "crewai",
            "google-genai",
            "google-generativeai",
            "langgraph",
            "litellm",
            "mcp",
            "openai",
            "openai-agents",
            "smolagents",
        ]
    }
)

DEFAULT_OTEL_ATTRIBUTE_COUNT_LIMIT = 4096

MAX_METADATA_FIELDS = 25
MAX_METADATA_KEY_CHARS = 40
MAX_METADATA_VALUE_CHARS = 100

OTEL_NAMESPACE = "atla"

LIB_VERSIONS_MARK = f"{OTEL_NAMESPACE}.debug.versions"
METADATA_MARK = f"{OTEL_NAMESPACE}.metadata"
SUCCESS_MARK = f"{OTEL_NAMESPACE}.mark.success"
VERSION_MARK = f"{OTEL_NAMESPACE}.sdk.version"

OTEL_MODULE_NAME = "atla_insights"
OTEL_TRACES_ENDPOINT = "https://logfire-eu.pydantic.dev/v1/traces"

SUPPORTED_LLM_FORMAT = Literal["anthropic", "bedrock", "openai"]
SUPPORTED_LLM_PROVIDER = Literal["anthropic", "google-genai", "litellm", "openai"]
LLM_PROVIDER_TYPE = Union[Sequence[SUPPORTED_LLM_PROVIDER], SUPPORTED_LLM_PROVIDER]
