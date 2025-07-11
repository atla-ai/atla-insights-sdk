"""Agent framework instrumentation logic."""

from atla_insights.frameworks.agno import instrument_agno, uninstrument_agno
from atla_insights.frameworks.baml import instrument_baml, uninstrument_baml
from atla_insights.frameworks.crewai import instrument_crewai, uninstrument_crewai
from atla_insights.frameworks.langchain import (
    instrument_langchain,
    uninstrument_langchain,
)
from atla_insights.frameworks.mcp import instrument_mcp, uninstrument_mcp
from atla_insights.frameworks.openai_agents import (
    instrument_openai_agents,
    uninstrument_openai_agents,
)
from atla_insights.frameworks.smolagents import (
    instrument_smolagents,
    uninstrument_smolagents,
)

__all__ = [
    "instrument_agno",
    "instrument_baml",
    "instrument_crewai",
    "instrument_langchain",
    "instrument_mcp",
    "instrument_openai_agents",
    "instrument_smolagents",
    "uninstrument_agno",
    "uninstrument_baml",
    "uninstrument_crewai",
    "uninstrument_langchain",
    "uninstrument_mcp",
    "uninstrument_openai_agents",
    "uninstrument_smolagents",
]
