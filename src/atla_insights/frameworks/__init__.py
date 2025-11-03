"""Agent framework instrumentation logic."""

from atla_insights.frameworks.agno import instrument_agno, uninstrument_agno
from atla_insights.frameworks.baml import instrument_baml, uninstrument_baml
from atla_insights.frameworks.claude_agent_sdk import (
    instrument_claude_agent_sdk,
    uninstrument_claude_agent_sdk,
)
from atla_insights.frameworks.claude_code_sdk import (
    instrument_claude_code_sdk,
    uninstrument_claude_code_sdk,
)
from atla_insights.frameworks.crewai import instrument_crewai, uninstrument_crewai
from atla_insights.frameworks.google_adk import (
    instrument_google_adk,
    uninstrument_google_adk,
)
from atla_insights.frameworks.langchain import (
    instrument_langchain,
    uninstrument_langchain,
)
from atla_insights.frameworks.mcp import instrument_mcp, uninstrument_mcp
from atla_insights.frameworks.openai_agents import (
    instrument_openai_agents,
    uninstrument_openai_agents,
)
from atla_insights.frameworks.pydantic_ai import (
    instrument_pydantic_ai,
    uninstrument_pydantic_ai,
)
from atla_insights.frameworks.smolagents import (
    instrument_smolagents,
    uninstrument_smolagents,
)

__all__ = [
    "instrument_agno",
    "instrument_baml",
    "instrument_claude_agent_sdk",
    "instrument_claude_code_sdk",
    "instrument_crewai",
    "instrument_google_adk",
    "instrument_langchain",
    "instrument_mcp",
    "instrument_openai_agents",
    "instrument_pydantic_ai",
    "instrument_smolagents",
    "uninstrument_agno",
    "uninstrument_baml",
    "uninstrument_claude_agent_sdk",
    "uninstrument_claude_code_sdk",
    "uninstrument_crewai",
    "uninstrument_google_adk",
    "uninstrument_langchain",
    "uninstrument_mcp",
    "uninstrument_openai_agents",
    "uninstrument_pydantic_ai",
    "uninstrument_smolagents",
]
