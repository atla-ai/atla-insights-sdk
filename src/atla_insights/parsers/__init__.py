"""Parsers for the atla_insights package."""

from atla_insights.constants import SUPPORTED_LLM_FORMAT
from atla_insights.parsers.base import BaseParser


def get_llm_parser(llm_provider: SUPPORTED_LLM_FORMAT) -> BaseParser:
    """Get the LLM parser."""
    match llm_provider:
        case "anthropic":
            from atla_insights.parsers.parse_anthropic import AnthropicParser

            return AnthropicParser()
        case "bedrock":
            from atla_insights.parsers.parse_bedrock import BedrockParser

            return BedrockParser()
        case "openai":
            from atla_insights.parsers.parse_openai import OpenAIChatCompletionParser

            return OpenAIChatCompletionParser()
        case _:
            raise ValueError(f"Unsupported LLM provider: {llm_provider}")


__all__ = ["get_llm_parser"]
