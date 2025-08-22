"""Atla package for PyPI distribution."""

from atla_insights.client import Client
from atla_insights.custom_metrics import get_custom_metrics, set_custom_metrics
from atla_insights.experiments import run_experiment
from atla_insights.frameworks import (
    instrument_agno,
    instrument_baml,
    instrument_claude_code_sdk,
    instrument_crewai,
    instrument_langchain,
    instrument_mcp,
    instrument_openai_agents,
    instrument_smolagents,
    uninstrument_agno,
    uninstrument_baml,
    uninstrument_claude_code_sdk,
    uninstrument_crewai,
    uninstrument_langchain,
    uninstrument_mcp,
    uninstrument_openai_agents,
    uninstrument_smolagents,
)
from atla_insights.instrument import instrument
from atla_insights.llm_providers import (
    instrument_anthropic,
    instrument_bedrock,
    instrument_google_genai,
    instrument_litellm,
    instrument_openai,
    uninstrument_anthropic,
    uninstrument_bedrock,
    uninstrument_google_genai,
    uninstrument_litellm,
    uninstrument_openai,
)
from atla_insights.main import configure
from atla_insights.marking import mark_failure, mark_success
from atla_insights.metadata import get_metadata, set_metadata
from atla_insights.suppression import enable_instrumentation, suppress_instrumentation
from atla_insights.tool import tool

__all__ = [
    "AtlaInsightsClient",
    "Client",
    "configure",
    "enable_instrumentation",
    "get_custom_metrics",
    "get_metadata",
    "instrument",
    "instrument_agno",
    "instrument_anthropic",
    "instrument_baml",
    "instrument_bedrock",
    "instrument_claude_code_sdk",
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
    "run_experiment",
    "set_custom_metrics",
    "set_metadata",
    "suppress_instrumentation",
    "tool",
    "uninstrument_agno",
    "uninstrument_anthropic",
    "uninstrument_baml",
    "uninstrument_bedrock",
    "uninstrument_claude_code_sdk",
    "uninstrument_crewai",
    "uninstrument_google_genai",
    "uninstrument_langchain",
    "uninstrument_litellm",
    "uninstrument_mcp",
    "uninstrument_openai",
    "uninstrument_openai_agents",
    "uninstrument_smolagents",
]
