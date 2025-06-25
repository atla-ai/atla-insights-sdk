"""Atla package for PyPI distribution."""

from logfire import instrument

from atla_insights._main import (
    configure,
    get_metadata,
    mark_failure,
    mark_success,
    set_metadata,
)
from atla_insights._tool import tool
from atla_insights.frameworks import (
    instrument_agno,
    instrument_crewai,
    instrument_langchain,
    instrument_mcp,
    instrument_openai_agents,
    instrument_smolagents,
    uninstrument_agno,
    uninstrument_crewai,
    uninstrument_langchain,
    uninstrument_mcp,
    uninstrument_openai_agents,
    uninstrument_smolagents,
)
from atla_insights.llm_providers import (
    instrument_anthropic,
    instrument_google_genai,
    instrument_litellm,
    instrument_openai,
    uninstrument_anthropic,
    uninstrument_google_genai,
    uninstrument_litellm,
    uninstrument_openai,
)

__all__ = [
    "configure",
    "get_metadata",
    "instrument",
    "instrument_agno",
    "instrument_anthropic",
    "instrument_crewai",
    "instrument_google_genai",
    "instrument_langchain",
    "instrument_litellm",
    "instrument_mcp",
    "instrument_openai",
    "instrument_openai_agents",
    "instrument_smolagents",
    "mark_failure",
    "mark_success",
    "set_metadata",
    "tool",
    "uninstrument_agno",
    "uninstrument_anthropic",
    "uninstrument_crewai",
    "uninstrument_google_genai",
    "uninstrument_langchain",
    "uninstrument_litellm",
    "uninstrument_mcp",
    "uninstrument_openai",
    "uninstrument_openai_agents",
    "uninstrument_smolagents",
]
